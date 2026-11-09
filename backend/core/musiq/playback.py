"""This module handles playback flow of music."""

from __future__ import annotations

import datetime
import logging
import os
import random
import time
from typing import Optional, Tuple

from django.conf import settings as conf
from django.db import connection, transaction
from django.utils import timezone

from core import models, redis, user_manager
from core.musiq import musiq
from core.settings import storage
from core.tasks import app
from core.musiq import song_utils
from core.models import CurrentSong

queue_changed = redis.Event("queue_changed")

queue = models.QueuedSong.objects


class PlaybackError(Exception):
    pass


def start() -> None:
    """Initializes this module by starting the playback."""
    paused = storage.get("paused")
    redis.put("paused", paused)
    _loop.delay()


class Playback:
    """Class containing all playback related methods."""

    def __init__(self):
        from core.musiq.fake_player import FakePlayer

        redis.put("playing", False)

        queue.delete_placeholders()

        self.players = {
            "fake": FakePlayer(),
        }

        if redis.get("spotify_available"):
            from core.musiq.spotify_player import SpotifyPlayer

            self.players["spotify"] = SpotifyPlayer()
        if redis.get("mopidy_available"):
            from core.musiq.mopidy_player import MopidyPlayer

            self.players["mopidy"] = MopidyPlayer()

        if redis.get("spotify_available") and storage.get("output").startswith(
            "spotify-"
        ):
            redis.put("active_player", "spotify")
        elif redis.get("mopidy_available"):
            redis.put("active_player", "mopidy")
        else:
            redis.put("active_player", "fake")

    def player(self):
        return self.players[redis.get("active_player")]

    def _get_next_song(self) -> Tuple[Optional[models.CurrentSong], bool]:
        """Returns the next song that should be played, or None if no song should be played.
        Additionally returns whether the song was recovered from the database (True)
        or dequeued from the queue (False)."""
        # TODO: is this playback_started clear necessary?
        # self.playback_started.clear()

        if models.CurrentSong.objects.exists():
            # recover interrupted song from database
            return models.CurrentSong.objects.get(), True

        if queue.count() == 0:
            queue_changed.wait()
            queue_changed.clear()

            # restart the loop to check again whether songs are available
            # in case of a false wakeup this causes as to wait again
            return None, False

        # select the next song depending on settings
        song: Optional[models.QueuedSong]
        if storage.get("interactivity") in [
            storage.Interactivity.upvotes_only,
            storage.Interactivity.full_voting,
        ]:
            with transaction.atomic():
                song = queue.confirmed().order_by("-votes", "index")[0]
                song_id = song.id
                queue.remove(song.id)
        elif storage.get("shuffle"):
            confirmed = queue.confirmed()
            index = random.randint(0, confirmed.count() - 1)
            song_id = confirmed[index].id
            song = queue.remove(song_id)
        else:
            # move the first song in the queue into the current song
            song_id, song = queue.dequeue()

        if song is None:
            # either the semaphore didn't match up with the actual count
            # of songs in the queue or a race condition occured
            logging.warning("dequeued on empty list")
            return None, False

        assert song.internal_url
        current_song = models.CurrentSong.objects.create(
            queue_key=song_id,
            manually_requested=song.manually_requested,
            votes=song.votes,
            internal_url=song.internal_url,
            external_url=song.external_url,
            stream_url=song.stream_url,
            artist=song.artist,
            title=song.title,
            duration=song.duration,
        )

        handle_autoplay()

        try:
            archived_song = models.ArchivedSong.objects.get(
                url=current_song.external_url
            )
            votes: Optional[int]
            if storage.get("interactivity") in [
                storage.Interactivity.upvotes_only,
                storage.Interactivity.full_voting,
            ]:
                votes = current_song.votes
            else:
                votes = None
            if storage.get("logging_enabled"):
                models.PlayLog.objects.create(
                    song=archived_song,
                    manually_requested=current_song.manually_requested,
                    votes=votes,
                )
        except (
            models.ArchivedSong.DoesNotExist,
            models.ArchivedSong.MultipleObjectsReturned,
        ):
            pass

        return current_song, False

    @staticmethod
    def _catch_up(current_song: models.CurrentSong, recovered: bool) -> Optional[int]:
        catch_up = None

        if recovered:
            # continue with the current song (approximately) where we last left
            if redis.get("paused"):
                catch_up = round(
                    (current_song.last_paused - current_song.created).total_seconds()
                    * 1000
                )
            else:
                catch_up = round(
                    (timezone.now() - current_song.created).total_seconds() * 1000
                )
            if catch_up > current_song.duration * 1000:
                catch_up = -1

        return catch_up

    def _wait_until_song_end(self) -> bool:
        """Wait until the song is over.
        Returns True when finished without errors, False otherwise."""
        # This is the event based approach. Unfortunately too error-prone.
        # If mopidy crashes/restarts for example, no track_playback_ended event is sent
        # playback_ended.wait()
        error = False
        while True:
            current_song = CurrentSong.objects.get()
            try:
                if self.player().should_stop_waiting(error):
                    break
            except PlaybackError:
                error = True
            paused = redis.get("paused")
            if paused:
                # stay in the loop, the song won't end while paused
                # progress = (current_song.last_paused - current_song.created).total_seconds()
                pass
            else:
                progress = (timezone.now() - current_song.created).total_seconds()
                if progress >= current_song.duration:
                    break
            # use internal timekeeping to decide when a song is over to lower mopidy performance use
            # current_song = models.CurrentSong.objects.get()
            # if (timezone.now() - current_song.created).total_seconds() > current_song.duration:
            #    break
            time.sleep(0.1)
            if redis.get("stop_playback_loop"):
                # in order to stop the playback thread, return False, making the main loop restart.
                # it will check this variable again and terminate itself.
                return False
        return not error

    def _song_finished(self, current_song: models.CurrentSong) -> None:
        """Handles things that might need to happen after a song ended, like repeat."""
        if storage.get("repeat"):
            queue.enqueue(
                {
                    "artist": current_song.artist,
                    "title": current_song.title,
                    "duration": current_song.duration,
                    "internal_url": current_song.internal_url,
                    "external_url": current_song.external_url,
                    "stream_url": current_song.stream_url,
                },
                False,
                enqueue_first=False,
            )
            queue_changed.set()

        musiq.update_state()

    def loop(self) -> None:
        """The main loop of the player.
        Takes a song from the queue and plays it until it is finished."""

        while True:
            if redis.get("playback_error"):
                # sleep for a short while so continuing errors don't lead to busy loops
                time.sleep(0.5)
                continue

            if redis.get("stop_playback_loop"):
                break

            current_song, recovered = self._get_next_song()
            if current_song is None:
                continue

            catch_up = self._catch_up(current_song, recovered)

            try:
                self.player().start_song(current_song, catch_up)
            except PlaybackError:
                # when a song can't be started, pause the playback
                # and have the user restart playback manually after fixing the error
                musiq.controller._pause()
                musiq.update_state()
                continue
            redis.put("playing", True)

            musiq.update_state()

            # don't wait for the song to end if catch_up is negative (=the song should be skipped)
            if catch_up is None or catch_up >= 0:
                if not self._wait_until_song_end():
                    # there was an error while waiting for the song to end
                    # This happens when we could not connect to mopidy (ConnectionError)
                    # We do not delete the current song but recover its state by restarting the loop
                    storage.put("paused", False)
                    redis.put("paused", False)
                    redis.put("playing", False)
                    continue
            # Allowing new songs to start playing while paused introduces many edge cases
            # Instead of dealing with them, always start playback when skipping a paused song
            storage.put("paused", False)
            redis.put("paused", False)
            redis.put("playing", False)

            current_song.delete()

            self._song_finished(current_song)


@app.task
def _loop() -> None:
    playback = Playback()
    playback.loop()
    connection.close()


def handle_autoplay(url: Optional[str] = None) -> None:
    """Checks whether to add a song by autoplay and does so if necessary.
    :param url: if given, this url is used to find the next autoplayed song.
    Otherwise, the current song is used."""
    if storage.get("autoplay") and models.QueuedSong.objects.count() == 0:
        if url is None:
            # if no url was specified, use the one of the current song
            try:
                current_song = models.CurrentSong.objects.get()
                url = current_song.external_url
            except (
                models.CurrentSong.DoesNotExist,
                models.CurrentSong.MultipleObjectsReturned,
            ):
                return

        from core.musiq.song_provider import SongProvider

        provider = SongProvider.create(external_url=url)
        try:
            suggestion = provider.get_suggestion()
            # The player loop is not restarted after error automatically.
            # As this function can raise several exceptions (it might do networking)
            # we catch every exception to make sure the loop keeps running
        except Exception as error:  # pylint: disable=broad-except
            logging.exception("error during suggestions for %s: %s", url, error)
        else:
            provider = SongProvider.create(external_url=suggestion)
            provider.request("", archive=False, manually_requested=False)


def stop() -> None:
    """Stops the playback main loop, only used for tests."""
    redis.put("stop_playback_loop", True)
    queue_changed.set()

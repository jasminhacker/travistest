"""This module handles the suggestions when starting to
type into the input field on the musiq page."""

from __future__ import annotations

import random
from typing import Dict, Union, List

from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponseBadRequest
from django.http.response import JsonResponse, HttpResponse
from watson import search as watson

import core.musiq.song_utils as song_utils
import core.settings.storage as storage
from core import redis
from core.models import ArchivedPlaylist, ArchivedSong
from core.musiq.song_provider import SongProvider


def random_suggestion(request: WSGIRequest) -> HttpResponse:
    """This method returns a random suggestion from the database.
    Depending on the value of :param playlist:,
    either a previously pushed playlist or song is returned."""
    suggest_playlist = request.GET["playlist"] == "true"
    if not suggest_playlist:
        if ArchivedSong.objects.count() == 0:
            return HttpResponseBadRequest("No songs to suggest from")
        index = random.randint(0, ArchivedSong.objects.count() - 1)
        song = ArchivedSong.objects.all()[index]
        return JsonResponse({"suggestion": song.displayname(), "key": song.id})

    # exclude radios from suggestions
    remaining_playlists = (
        ArchivedPlaylist.objects.all()
        .exclude(list_id__startswith="RD")
        .exclude(list_id__contains="&list=RD")
    )
    if remaining_playlists.count() == 0:
        return HttpResponseBadRequest("No playlists to suggest from")
    index = random.randint(0, remaining_playlists.count() - 1)
    playlist = remaining_playlists.all()[index]
    return JsonResponse({"suggestion": playlist.title, "key": playlist.id})


def _online_suggestions(query, suggest_playlist) -> List[Dict[str, Union[str, int]]]:
    results: List[Dict[str, Union[str, int]]] = []
    if storage.get("online_suggestions") and redis.get("has_internet"):
        if storage.get("spotify_enabled") and storage.get("spotify_suggestions") > 0:
            from core.musiq.spotify import Spotify

            spotify_suggestions = Spotify().get_search_suggestions(
                query, suggest_playlist
            )
            spotify_suggestions = spotify_suggestions[
                : storage.get("spotify_suggestions")
            ]
            for suggestion, external_url in spotify_suggestions:
                results.append(
                    {"key": external_url, "value": suggestion, "type": "spotify-online"}
                )

        if (
            storage.get("soundcloud_enabled")
            and storage.get("soundcloud_suggestions") > 0
        ):
            from core.musiq.soundcloud import Soundcloud

            soundcloud_suggestions = Soundcloud().get_search_suggestions(query)
            soundcloud_suggestions = soundcloud_suggestions[
                : storage.get("soundcloud_suggestions")
            ]
            for suggestion in soundcloud_suggestions:
                results.append(
                    {"key": -1, "value": suggestion, "type": "soundcloud-online"}
                )

        if storage.get("jamendo_enabled") and storage.get("jamendo_suggestions") > 0:
            from core.musiq.jamendo import Jamendo

            jamendo_suggestions = Jamendo().get_search_suggestions(query)
            jamendo_suggestions = jamendo_suggestions[
                : storage.get("jamendo_suggestions")
            ]
            for suggestion in jamendo_suggestions:
                results.append(
                    {"key": -1, "value": suggestion, "type": "jamendo-online"}
                )

        if storage.get("youtube_enabled") and storage.get("youtube_suggestions") > 0:
            from core.musiq.youtube import Youtube

            youtube_suggestions = Youtube().get_search_suggestions(query)
            youtube_suggestions = youtube_suggestions[
                : storage.get("youtube_suggestions")
            ]
            for suggestion in youtube_suggestions:
                results.append(
                    {"key": -1, "value": suggestion, "type": "youtube-online"}
                )
    return results


def get_suggestions(request: WSGIRequest) -> JsonResponse:
    """Returns suggestions for a given query.
    Combines online and offline suggestions."""
    query = request.GET["term"]
    suggest_playlist = request.GET["playlist"] == "true"

    if storage.get("new_music_only") and not suggest_playlist:
        return JsonResponse([], safe=False)

    results = _online_suggestions(query, suggest_playlist)

    if suggest_playlist:
        search_results = watson.search(query, models=(ArchivedPlaylist,))[
            : storage.get("number_of_suggestions")
        ]

        for playlist in search_results:
            playlist_info = playlist.meta
            archived_playlist = ArchivedPlaylist.objects.get(id=playlist_info["id"])
            result_dict: Dict[str, Union[str, int]] = {
                "key": playlist_info["id"],
                "value": playlist_info["title"],
                "counter": playlist.object.counter,
                "type": song_utils.determine_playlist_type(archived_playlist),
            }
            results.append(result_dict)
    else:
        search_results = watson.search(query, models=(ArchivedSong,))[
            : storage.get("number_of_suggestions")
        ]

        for search_result in search_results:
            song_info = search_result.meta

            if song_utils.is_forbidden(song_info["artist"]) or song_utils.is_forbidden(
                song_info["title"]
            ):
                continue

            try:
                provider = SongProvider.create(external_url=song_info["url"])
            except NotImplementedError:
                # For this song a provider is necessary that is not available
                # e.g. the song was played before, but the provider was disabled
                continue
            cached = provider.check_cached()
            # don't suggest local songs if they are not cached (=not at expected location)
            if not cached and provider.type == "local":
                continue
            # don't suggest online songs when we don't have internet
            if not redis.get("has_internet") and not cached:
                continue
            # don't suggest youtube songs if it was disabled
            if not storage.get("youtube_enabled") and provider.type == "youtube":
                continue
            # don't suggest spotify songs if we are not logged in
            if not storage.get("spotify_enabled") and provider.type == "spotify":
                continue
            # don't suggest soundcloud songs if we are not logged in
            if not storage.get("soundcloud_enabled") and provider.type == "soundcloud":
                continue
            # don't suggest jamendo songs if we are not logged in
            if not storage.get("jamendo_enabled") and provider.type == "jamendo":
                continue
            result_dict = {
                "key": song_info["id"],
                "value": song_utils.displayname(
                    song_info["artist"], song_info["title"]
                ),
                "counter": search_result.object.counter,
                "type": provider.type,
            }
            results.append(result_dict)

    return JsonResponse(results, safe=False)
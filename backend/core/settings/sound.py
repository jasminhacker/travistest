"""This module handles all settings related to sound output."""

from __future__ import annotations

import logging
import re
import subprocess
import time
from threading import Thread
from typing import Optional

from django.conf import settings as conf
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse

from core import redis, util
from core.models import CurrentSong
from core.settings import settings, storage, system
from core.settings.settings import control
from core.tasks import app

# to control that only one bluetoothctl process is active at a time
# we use a redis variable instead of a redis lock
# we need to release the lock(=kill the process) in a different request than the one that started it
# this made using the lock complicated, and only one admin should be using the page at once anyway

# bluetooth_devices: List[Dict[str, str]] = []


@control
def list_outputs(_request: WSGIRequest) -> JsonResponse:
    """Returns a list of all sound output devices currently available."""
    fakesink = {"id": "fakesink", "name": "No playback"}
    mopidy = {"id": "mopidy", "name": "Mopidy playback"}
    client = {"id": "client", "name": "Browser playback"}

    sinks = [fakesink, client]
    if redis.get("mopidy_available"):
        sinks.append(mopidy)
    if storage.get("spotify_enabled"):
        from core.musiq.spotify import Spotify

        for device in Spotify.api.devices()["devices"]:
            sinks.append(
                {"id": f"spotify-{device['id']}", "name": f"[spotify] {device['name']}"}
            )

    return JsonResponse(sinks, safe=False)


def _set_output(output: str) -> HttpResponse:
    use_spotify_player = False

    if output.startswith("spotify-") and storage.get("spotify_enabled"):
        output = output[len("spotify-") :]
        from core.musiq.spotify import Spotify

        from spotipy import SpotifyException

        try:
            Spotify.api.transfer_playback(output)
        except SpotifyException:
            return HttpResponseBadRequest("Device not available")
        use_spotify_player = True
    else:
        logging.warning("Unknown sound output requested. Setting to fakesink.")

    if use_spotify_player:
        redis.put("active_player", "spotify")
    elif not redis.get("mopidy_available"):
        redis.put("active_player", "fake")
    else:
        redis.put("active_player", "mopidy")

    return HttpResponse(
        "Output was set. Restarting the current song might be necessary."
    )


@control
def set_output(request: WSGIRequest) -> HttpResponse:
    """Sets the given device as default output device."""
    output = request.POST.get("value")
    if not output:
        return HttpResponseBadRequest("No output selected")

    if output == storage.get("output"):
        return HttpResponseBadRequest("Output unchanged")

    storage.put("output", output)

    return _set_output(output)


@control
def delete_current_song(_request: WSGIRequest) -> HttpResponse:
    """Force skips the current song by deleting it from the database."""
    try:
        current_song = CurrentSong.objects.get()
        current_song.delete()
        return HttpResponse()
    except CurrentSong.DoesNotExist:
        return HttpResponseBadRequest("No song playing")

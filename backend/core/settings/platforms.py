"""This module handles all settings regarding the music platforms."""

from __future__ import annotations

import importlib.util
import os
import subprocess
from typing import cast

from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse, HttpResponseBadRequest

from django.conf import settings as conf
from core import redis
from core.settings import library, storage, system
from core.settings.settings import control
from core.settings.storage import PlatformEnabled
from core.util import extract_value, strtobool


def start() -> None:
    """Initializes this module by checking which platforms are available to use."""

    # mopidy is available if the server can be connected to
    import socket

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    location = (conf.MOPIDY_HOST, int(conf.MOPIDY_PORT))
    mopidy_available = True
    try:
        check = sock.connect_ex(location)
        if check != 0:
            mopidy_available = False
    except (ConnectionRefusedError, socket.gaierror):
        # check for gaierror because docker compose setups might not be able to resolve the hostname
        mopidy_available = False
    finally:
        sock.close()
    redis.put("mopidy_available", mopidy_available)

    # local songs are enabled if a library is set
    local_enabled = os.path.islink(library.get_library_path())
    storage.put("local_enabled", local_enabled)

    # in the docker container all dependencies are installed
    # TODO: was this an issue in docker?
    youtube_available = importlib.util.find_spec("yt_dlp") is not None
    redis.put("youtube_available", youtube_available)
    if not youtube_available:
        # if youtube is not available, overwrite the database to disable it
        storage.put("youtube_enabled", False)

    spotify_available = importlib.util.find_spec("spotipy") is not None
    redis.put("spotify_available", spotify_available)
    if not spotify_available:
        storage.put("spotify_enabled", False)

    # Jamendo as client streaming is always available
    jamendo_available = True
    redis.put("jamendo_available", jamendo_available)
    if not jamendo_available:
        storage.put("jamendo_enabled", False)


@control
def set_youtube_enabled(request: WSGIRequest) -> HttpResponse:
    """Enables or disables youtube to be used as a song provider."""
    value, response = extract_value(request.POST)
    storage.put("youtube_enabled", strtobool(value))
    return response


@control
def set_youtube_suggestions(request: WSGIRequest) -> HttpResponse:
    """Sets the number of online suggestions from youtube to be shown."""
    value, response = extract_value(request.POST)
    storage.put("youtube_suggestions", int(value))
    return response


def _set_extension_enabled(extension, enabled) -> HttpResponse:
    if enabled:
        response = HttpResponse(f"Enabled {extension}")
    else:
        response = HttpResponse(f"Disabled {extension}")
    assert extension in ["local", "youtube", "spotify", "jamendo"]
    storage.put(cast(PlatformEnabled, f"{extension}_enabled"), enabled)
    return response


@control
def set_spotify_enabled(request: WSGIRequest) -> HttpResponse:
    """Enables or disables spotify to be used as a song provider.
    Makes sure mopidy has correct spotify configuration."""
    value, _ = extract_value(request.POST)
    mopidy_response = _set_extension_enabled("spotify", strtobool(value))

    if not strtobool(value):
        return mopidy_response
    else:
        # Check whether Spotify device authorization works
        from core.musiq.spotify import Spotify
        from spotipy.oauth2 import SpotifyOauthError

        try:
            api = Spotify.api
            api.devices()
        except SpotifyOauthError as e:
            message = e.error_description or e
            login_successful = False
        else:
            message = "Login successful"
            login_successful = True
        if type(mopidy_response) is HttpResponseBadRequest and not login_successful:
            return HttpResponseBadRequest(message)
        else:
            # enable spotify if at least one option works
            storage.put(cast(PlatformEnabled, f"spotify_enabled"), True)
            return HttpResponse(message)


@control
def set_spotify_suggestions(request: WSGIRequest) -> HttpResponse:
    """Sets the number of online suggestions from spotify to be shown."""
    value, response = extract_value(request.POST)
    storage.put("spotify_suggestions", int(value))
    return response


@control
def set_spotify_credentials(request: WSGIRequest) -> HttpResponse:
    """Update spotify credentials."""
    client_id = request.POST.get("client_id")
    client_secret = request.POST.get("client_secret")
    redirect_uri = request.POST.get("redirect_uri")
    authorized_url = request.POST.get("authorized_url")

    if not client_id or not client_secret or not redirect_uri or not authorized_url:
        return HttpResponseBadRequest("All fields are required")

    storage.put("spotify_client_id", client_id)
    storage.put("spotify_client_secret", client_secret)
    storage.put("spotify_redirect_uri", redirect_uri)
    storage.put("spotify_authorized_url", authorized_url)

    from core.musiq.spotify import Spotify

    Spotify.create_api()
    return HttpResponse("Updated credentials")


@control
def set_jamendo_enabled(request: WSGIRequest) -> HttpResponse:
    """Enables or disables jamendo to be used as a song provider.
    Makes sure mopidy has correct jamendo configuration."""
    value, _ = extract_value(request.POST)
    return _set_extension_enabled("jamendo", strtobool(value))


@control
def set_jamendo_suggestions(request: WSGIRequest) -> HttpResponse:
    """Sets the number of online suggestions from jamendo to be shown."""
    value, response = extract_value(request.POST)
    storage.put("jamendo_suggestions", int(value))
    return response


@control
def set_jamendo_credentials(request: WSGIRequest) -> HttpResponse:
    """Update jamendo credentials."""
    client_id = request.POST.get("client_id")

    if not client_id:
        return HttpResponseBadRequest("All fields are required")

    storage.put("jamendo_client_id", client_id)

    return HttpResponse("Updated credentials")

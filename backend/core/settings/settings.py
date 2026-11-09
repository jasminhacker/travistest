"""This module contains everything related to the settings and configuration of the server."""

from __future__ import annotations

import os
import subprocess
from functools import wraps
from typing import Any, Callable, Dict, Optional

from django.conf import settings as conf
from django.contrib.auth.decorators import user_passes_test
from django.core.handlers.wsgi import WSGIRequest

# JsonResponse needs to be imported here so types can resolved through the decorator?
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render

from core import base, redis, tasks, user_manager
from core.settings.storage import get
from core.state_handler import send_state


def control(
    func: Callable[[WSGIRequest], Optional[HttpResponse]],
) -> Callable[[WSGIRequest], HttpResponse]:
    """A decorator that makes sure that only the admin changes a setting."""

    def _decorator(request: WSGIRequest) -> HttpResponse:
        if not user_manager.is_admin(request.user):
            return HttpResponseForbidden()
        response = func(request)
        update_state()
        if response is not None:
            return response
        return HttpResponse()

    return wraps(func)(_decorator)


def state_dict() -> Dict[str, Any]:
    """Extends the base state with settings-specific information and returns it."""
    state = base.state_dict()

    settings_state: Dict[str, Any] = {}
    settings_state["interactivity"] = get("interactivity")
    settings_state["colorIndication"] = get("color_indication")
    settings_state["ipChecking"] = get("ip_checking")
    settings_state["downvotesToKick"] = get("downvotes_to_kick")
    settings_state["loggingEnabled"] = get("logging_enabled")
    settings_state["hashtagsActive"] = get("hashtags_active")
    settings_state["privilegedStream"] = get("privileged_stream")
    settings_state["onlineSuggestions"] = get("online_suggestions")
    settings_state["numberOfSuggestions"] = get("number_of_suggestions")
    settings_state["connectivityHost"] = get("connectivity_host")
    settings_state["hasInternet"] = redis.get("has_internet")
    settings_state["newMusicOnly"] = get("new_music_only")
    settings_state["enqueueFirst"] = get("enqueue_first")
    settings_state["songCooldown"] = get("song_cooldown")
    settings_state["maxPlaylistItems"] = get("max_playlist_items")
    settings_state["maxQueueLength"] = get("max_queue_length")
    settings_state["additionalKeywords"] = get("additional_keywords")
    settings_state["forbiddenKeywords"] = get("forbidden_keywords")
    settings_state["peopleToParty"] = get("people_to_party")

    settings_state["youtubeEnabled"] = get("youtube_enabled")
    settings_state["youtubeSuggestions"] = get("youtube_suggestions")

    settings_state["spotifyEnabled"] = get("spotify_enabled")
    settings_state["spotifySuggestions"] = get("spotify_suggestions")

    settings_state["jamendoEnabled"] = get("jamendo_enabled")
    settings_state["jamendoSuggestions"] = get("jamendo_suggestions")

    settings_state["output"] = get("output")

    settings_state["scanProgress"] = redis.get("library_scan_progress")

    settings_state["youtubeConfigured"] = redis.get("youtube_available")
    settings_state["spotifyConfigured"] = redis.get("spotify_available")
    settings_state["jamendoConfigured"] = redis.get("jamendo_available")

    state["settings"] = settings_state
    return state


@user_passes_test(user_manager.is_admin)
def index(request: WSGIRequest) -> HttpResponse:
    """Renders the /settings page. Only admin is allowed to see this page."""
    from core import urls
    from core.settings import library

    context = base.context(request)
    context["urls"] = urls.settings_paths
    library_path = library.get_library_path()
    if os.path.islink(library_path):
        context["local_library"] = os.readlink(library_path)
    else:
        context["local_library"] = "/"
    context["version"] = conf.VERSION
    context["spotify_scope"] = (
        "user-read-playback-state user-modify-playback-state user-library-read playlist-read-private playlist-read-collaborative"
    )
    context["spotify_oauth_authorize_url"] = "https://accounts.spotify.com/authorize"
    return render(request, "settings.html", context)


def update_state() -> None:
    """Sends an update event to all connected clients."""
    send_state(state_dict())

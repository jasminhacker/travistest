"""This module contains all url endpoints and maps them to their corresponding functions."""

import inspect
from typing import Any, List, Union

from django.core.handlers.wsgi import WSGIRequest
from django.urls import URLPattern, URLResolver, include, path
from django.views.generic import RedirectView

from core import api
from core import base
from core.musiq import controller as musiq_controller
from core.musiq import musiq
from core.musiq import suggestions
from core.settings import analysis
from core.settings import basic
from core.settings import library
from core.settings import platforms
from core.settings import settings
from core.settings import sound
from core.settings import system
from core import state_handler

urlpatterns: List[Union[URLPattern, URLResolver]] = [
    path("", RedirectView.as_view(pattern_name="musiq", permanent=False), name="base"),
    path("musiq/", musiq.index, name="musiq"),
    path("settings/", settings.index, name="settings"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("login/", RedirectView.as_view(pattern_name="login", permanent=False)),
    path("logged-in/", base.logged_in, name="logged-in"),
    path("logout/", RedirectView.as_view(pattern_name="logout", permanent=False)),
    path(
        "api/",
        include(
            [
                path("version/", api.version, name="version"),
                path(
                    "musiq/",
                    include(
                        [
                            path("post_song/", api.post_song, name="post_song"),
                        ]
                    ),
                ),
            ]
        ),
    ),
]

urlmethods = [urlpattern.callback for urlpattern in urlpatterns]


def get_paths(objs: List[Any]) -> List[URLPattern]:
    """Iterates through the given objects and identifies all methods that serve http requests.
    A url pattern is generated for each of these methods,
    but only if no such path exists already in urlpatterns.
    Returns the list of url patterns."""
    paths = []
    for obj in objs:
        for name, method in inspect.getmembers(obj, inspect.isfunction):
            if name == "get_state":
                # the state url is an exception
                # it cannot be named after its method name, as every page has its own get_state
                continue
            if name.startswith("_"):
                # do not expose internal methods
                continue
            # use __annotations__ instead of get_type_hints, because the latter raised errors about
            # WSGIRequest not being defined in some configurations
            # string annotations are sufficient for our use case
            type_hints = method.__annotations__
            if "request" in type_hints:
                request_type = type_hints["request"]
            elif "_request" in type_hints:
                request_type = type_hints["_request"]
            else:
                continue
            if (
                request_type == "WSGIRequest" or issubclass(request_type, WSGIRequest)
            ) and method not in urlmethods:
                name = name.replace("_", "-")
                paths.append(path(name + "/", method, name=name))
    return paths


base_paths = get_paths([base])
musiq_paths = get_paths([musiq, musiq_controller, suggestions])
settings_paths = get_paths([basic, platforms, sound, library, analysis, system])

urlpatterns.append(
    path(
        "ajax/",
        include(
            [
                path("", include(base_paths)),
                path(
                    "musiq/state/",
                    state_handler.get_state,
                    {"module": musiq},
                    name="musiq-state",
                ),
                path("musiq/", include(musiq_paths)),
                path(
                    "settings/state/",
                    state_handler.get_state,
                    {"module": settings},
                    name="settings-state",
                ),
                path("settings/", include(settings_paths)),
            ]
        ),
    )
)

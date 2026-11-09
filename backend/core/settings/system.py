"""This module handles all settings related to system configuration."""

from __future__ import annotations

import configparser
import os
import re
import shutil
import subprocess
import sys
from typing import Dict, Optional, Tuple

import cachetools.func
import requests
from django.conf import settings
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse, HttpResponseBadRequest

from core import redis
from core.settings import storage
from core.settings.settings import control


@cachetools.func.ttl_cache(ttl=60 * 60 * 24)
def fetch_latest_version() -> Optional[str]:
    """Looks up the newest version number from PyPi and returns it."""
    if not redis.get("has_internet"):
        return None
    # https://github.com/pypa/pip/issues/9139
    # these subprocesses are expected to fail
    # move to pip index versions raveberry once that's not experimental anymore
    pip = subprocess.run(  # pylint: disable=subprocess-run-check
        "pip3 install --use-deprecated=legacy-resolver raveberry==nonexistingversion".split(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    if pip.returncode == 2:
        # pip does not know the --use-deprecated=legacy-resolver
        # probably an older version that does not need it
        pip = subprocess.run(  # pylint: disable=subprocess-run-check
            "pip3 install raveberry==nonexistingversion".split(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )

    # parse the newest version from pip output
    for line in pip.stderr.splitlines():
        if "from versions" in line:
            versions = [re.sub(r"[^0-9.]", "", token) for token in line.split()]
            versions = [version for version in versions if version]
            try:
                latest_version = versions[-1]
            except IndexError:
                return None
            return latest_version
    return None


@control
def get_latest_version(_request: WSGIRequest) -> HttpResponse:
    """Returns the newest version number of Raveberry from PyPi."""
    latest_version = fetch_latest_version()
    if latest_version is None:
        return HttpResponseBadRequest("Could not determine latest version.")
    return HttpResponse(latest_version)


@control
def get_changelog(_request: WSGIRequest) -> HttpResponse:
    """Retreives the changelog and returns it."""
    changelog = requests.get(
        "https://raw.githubusercontent.com/raveberry/raveberry/master/CHANGELOG.md"
    ).text
    return HttpResponse(changelog)

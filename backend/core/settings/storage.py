"""This module provides methods to access database settings."""

from ast import literal_eval
from typing import Union, Literal

from cachetools import TTLCache, cached

from core import models
from core.util import strtobool


class Interactivity:
    """An enum containing all possible interactivity level descriptions."""

    full_control = "Full Public Control"
    full_voting = "Up- and Downvoting"
    upvotes_only = "Upvotes Only"
    no_control = "No Control"


class Privileges:
    """An enum containing all privilege levels."""

    everybody = "Everybody"
    mod = "Mod and Admin"
    admin = "Admin Only"
    nobody = "Nobody"


PlatformEnabled = Literal
PlatformSuggestions = Literal

# maps key to default and type of value
defaults = {
    # basic settings
    "interactivity": Interactivity.full_control,
    "ip_checking": False,
    "color_indication": Privileges.nobody,
    "color_offset": 0.0,
    "next_color_index": 0,
    "downvotes_to_kick": 2,
    "logging_enabled": True,
    "hashtags_active": True,
    "privileged_stream": False,
    "online_suggestions": True,
    "number_of_suggestions": 20,
    "connectivity_host": "1.1.1.1",
    "new_music_only": False,
    "enqueue_first": False,
    "song_cooldown": 0.0,
    "max_download_size": 0.0,
    "max_playlist_items": 10,
    "max_queue_length": 0,
    "additional_keywords": "",
    "forbidden_keywords": "",
    "people_to_party": 3,
    # platforms
    "local_enabled": True,
    "youtube_enabled": True,
    "youtube_suggestions": 2,
    "spotify_enabled": False,
    "spotify_suggestions": 2,
    "spotify_client_id": "",
    "spotify_client_secret": "",
    "spotify_redirect_uri": "",
    "spotify_authorized_url": "",
    "spotipy_token_info": "",
    "jamendo_enabled": False,
    "jamendo_suggestions": 2,
    "jamendo_client_id": "",
    # sound
    "output": "",
    # playback
    "paused": False,
    "volume": 1.0,
    "shuffle": False,
    "repeat": False,
    "autoplay": False,
}

# Settings change very rarely, cache them to reduce database roundtrips.
# This is especially advantageous for suggestions which check whether platforms are enabled.
# There is a data inconsistency issue when a setting is changed in one process.
# Only that process would flush its cache, others would retain the stale value.
# However, with the daphne setup there is currently only one process handling requests,
# and settings are never changed outside a request (especially not in a celery worker).
# So this is fine as long as no additional daphne (or other) workers are used.
# However, settings are accessed in the playback worker.
# It accesses the "paused" state very often,
# so it is stored both in redis and the db.
# Alternatively, the cache flush could be communicated through redis.
cache: TTLCache = TTLCache(ttl=10, maxsize=128)


@cached(cache)
def get(key: str) -> Union[bool, int, float, str, tuple]:
    """This method returns the value for the given :param key:.
    Values of non-existing keys are set to their respective default value."""
    # values are stored as string in the database
    # cast the value to its respective type, defined by the default value, before returning it
    default = defaults[key]
    value = models.Setting.objects.get_or_create(
        key=key, defaults={"value": str(default)}
    )[0].value
    if type(default) is str:
        return str(value)
    if type(default) is int:
        return int(value)
    if type(default) is float:
        return float(value)
    if type(default) is bool:
        return strtobool(value)
    if type(default) is tuple:
        # evaluate the stored literal
        return literal_eval(value)
    raise ValueError(f"{key} not defined")


def put(key: str, value: Union[bool, int, float, str, tuple]) -> None:
    """This method sets the :param value: for the given :param key:."""
    default = defaults[key]
    setting = models.Setting.objects.get_or_create(
        key=key, defaults={"value": str(default)}
    )[0]
    setting.value = str(value)
    setting.save()
    cache.clear()

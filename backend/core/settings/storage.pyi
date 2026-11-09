from typing import Literal, overload

from cachetools import TTLCache

# Sometimes the storage functions are accessed dynamically.
# Comfort mypy by telling it the value will still be one of the specified ones.

class Interactivity:
        full_control = "Full Public Control"
        full_voting = "Up- and Downvoting"
        upvotes_only = "Upvotes Only"
        no_control = "No Control"

class Privileges:
        everybody = "Everybody"
        mod = "Mod and Admin"
        admin = "Admin Only"
        nobody = "Nobody"

PlatformEnabled = Literal[
    "local_enabled",
    "youtube_enabled",
    "spotify_enabled",
    "jamendo_enabled",
]

PlatformSuggestions = Literal[
    "youtube_suggestions",
    "spotify_suggestions",
    "jamendo_suggestions",
]


cache: TTLCache = TTLCache(ttl=10, maxsize=128)

@overload
def get(
    key: Literal[
        "ip_checking",
        "logging_enabled",
        "hashtags_active",
        "privileged_stream",
        "online_suggestions",
        "new_music_only",
        "enqueue_first",
        "local_enabled",
        "youtube_enabled",
        "spotify_enabled",
        "jamendo_enabled",
        "paused",
        "shuffle",
        "repeat",
        "autoplay",
    ]
) -> bool: ...
@overload
def get(
    key: Literal[
        "next_color_index",
        "downvotes_to_kick",
        "number_of_suggestions",
        "max_playlist_items",
        "max_queue_length",
        "people_to_party",
        "youtube_suggestions",
        "spotify_suggestions",
        "jamendo_suggestions",
        "wled_led_count",
        "wled_port",
    ]
) -> int: ...
@overload
def get(
    key: Literal[
        "color_offset",
        "song_cooldown",
        "max_download_size",
        "volume",
    ]
) -> float: ...
@overload
def get(
    key: Literal[
        "interactivity",
        "color_indication",
        "connectivity_host",
        "additional_keywords",
        "forbidden_keywords",
        "spotify_client_id",
        "spotify_client_secret",
        "spotify_redirect_uri",
        "spotify_authorized_url",
        "spotipy_token_info",
        "jamendo_client_id",
        "output",
    ]
) -> str: ...
@overload
def get(key: Literal["initial_resolution"]) -> tuple[int, int]: ...
@overload
def get(key: Literal["fixed_color"]) -> tuple[float, float, float]: ...
@overload
def put(
    key: Literal[
        "ip_checking",
        "logging_enabled",
        "hashtags_active",
        "privileged_stream",
        "online_suggestions",
        "new_music_only",
        "enqueue_first",
        "local_enabled",
        "youtube_enabled",
        "spotify_enabled",
        "jamendo_enabled",
        "paused",
        "shuffle",
        "repeat",
        "autoplay",
    ],
    value: bool,
) -> None: ...
@overload
def put(
    key: Literal[
        "next_color_index",
        "downvotes_to_kick",
        "number_of_suggestions",
        "max_playlist_items",
        "max_queue_length",
        "people_to_party",
        "youtube_suggestions",
        "spotify_suggestions",
        "jamendo_suggestions",
        "wled_led_count",
        "wled_port",
    ],
    value: int,
) -> None: ...
@overload
def put(
    key: Literal[
        "color_offset",
        "song_cooldown",
        "max_download_size",
        "volume",
    ],
    value: float,
) -> None: ...
@overload
def put(
    key: Literal[
        "interactivity",
        "color_indication",
        "connectivity_host",
        "additional_keywords",
        "forbidden_keywords",
        "spotify_client_id",
        "spotify_client_secret",
        "spotify_redirect_uri",
        "spotify_authorized_url",
        "spotipy_token_info",
        "jamendo_client_id",
        "output",
    ],
    value: str,
) -> None: ...
@overload
def put(key: Literal["initial_resolution"], value: tuple[int, int]) -> None: ...
@overload
def put(key: Literal["fixed_color"], value: tuple[float, float, float]) -> None: ...

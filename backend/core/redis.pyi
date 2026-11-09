from typing import Dict, List, Literal, Tuple, overload

from redis import Redis

connection: Redis

def start() -> None: ...

class Event:
    def __init__(self, name: str) -> None: ...
    def wait(self) -> None: ...
    def set(self) -> None: ...
    def clear(self) -> None: ...

@overload
def get(
    key: Literal[
        "playing",
        "paused",
        "playback_error",
        "stop_playback_loop",
        "has_internet",
        "mopidy_available",
        "youtube_available",
        "spotify_available",
        "jamendo_available",
    ]
) -> bool: ...
@overload
def get(
    key: Literal["last_user_count_update"]
) -> float: ...
@overload
def get(key: Literal["active_player", "library_scan_progress"]) -> str: ...
@overload
def get(key: Literal["last_requests"]) -> Dict[str, float]: ...
@overload
def put(
    key: Literal[
        "playing",
        "paused",
        "playback_error",
        "stop_playback_loop",
        "has_internet",
        "mopidy_available",
        "youtube_available",
        "spotify_available",
        "jamendo_available",
    ],
    value: bool,
) -> None: ...
@overload
def put(
    key: Literal["last_user_count_update"],
    value: float,
) -> None: ...
@overload
def put(key: Literal["active_player", "library_scan_progress"], value: str) -> None: ...
@overload
def put(key: Literal["last_requests"], value: Dict[str, float]) -> None: ...

import os

from django.urls import reverse

from core.models import Setting
from tests.music_test import MusicTest


class SpotifyTests(MusicTest):
    def setUp(self) -> None:
        try:
            # copy these from the instance where you signed in at http://localhost:8080/admin/core/setting
            # set - a  # automatically export all variables
            # source.env
            # set + a
            client_id = os.environ["SPOTIFY_CLIENT_ID"]
            client_secret = os.environ["SPOTIFY_CLIENT_SECRET"]
            redirect_uri = os.environ["SPOTIFY_REDIRECT_URI"]
            token_info = os.environ["SPOTIPY_TOKEN_INFO"]
        except KeyError:
            self.skipTest("No spotify credentials provided.")

        super().setUp()

        Setting.objects.update_or_create(
            key="spotify_client_id", defaults={"value": client_id}
        )
        Setting.objects.update_or_create(
            key="spotify_client_secret", defaults={"value": client_secret}
        )
        Setting.objects.update_or_create(
            key="spotify_redirect_uri", defaults={"value": redirect_uri}
        )
        Setting.objects.update_or_create(
            key="spotipy_token_info", defaults={"value": token_info}
        )

        self.client.post(reverse("set-spotify-enabled"), {"value": "true"})

    def test_query(self) -> None:
        self.client.post(
            reverse("request-music"),
            {
                "query": "Myuu Collapse",
                "playlist": "false",
                "platform": "spotify",
            },
        )
        current_song = self._poll_current_song()
        self.assertEqual(
            current_song["externalUrl"],
            "https://open.spotify.com/track/0o261w05EPiGfxNtVlWn6m",
        )
        self.assertEqual(current_song["artist"], "Myuu")
        self.assertEqual(current_song["title"], "Collapse")
        self.assertAlmostEqual(current_song["duration"], 200, delta=1)

    def test_url(self) -> None:
        self.client.post(
            reverse("request-music"),
            {
                "query": "https://open.spotify.com/track/0o261w05EPiGfxNtVlWn6m",
                "playlist": "false",
                "platform": "spotify",
            },
        )
        current_song = self._poll_current_song()
        self.assertEqual(
            current_song["externalUrl"],
            "https://open.spotify.com/track/0o261w05EPiGfxNtVlWn6m",
        )
        self.assertEqual(current_song["artist"], "Myuu")
        self.assertEqual(current_song["title"], "Collapse")
        self.assertAlmostEqual(current_song["duration"], 200, delta=1)

    def test_playlist_url(self) -> None:
        self.client.post(
            reverse("request-music"),
            {
                "query": "https://open.spotify.com/album/1d3X0w0kdfqcvOVNfnthhP",
                "playlist": "true",
                "platform": "spotify",
            },
        )
        state = self._poll_musiq_state(
            lambda state: state["musiq"]["currentSong"]
            and len(state["musiq"]["songQueue"]) == 4
            and all(song["internalUrl"] for song in state["musiq"]["songQueue"]),
            timeout=10,
        )
        self.assertEqual(
            state["musiq"]["currentSong"]["externalUrl"],
            "https://open.spotify.com/track/3uYgQ819EExqKhxr2ILFok",
        )
        self.assertEqual(
            state["musiq"]["songQueue"][0]["externalUrl"],
            "https://open.spotify.com/track/43TuwMfK9h8b0rtbkdWCYJ",
        )
        self.assertEqual(
            state["musiq"]["songQueue"][1]["externalUrl"],
            "https://open.spotify.com/track/7JsBddAbtHCjdEtMobVfyL",
        )
        self.assertEqual(
            state["musiq"]["songQueue"][2]["externalUrl"],
            "https://open.spotify.com/track/01Rk5ZPcMeQLxBEAcxZMju",
        )
        self.assertEqual(
            state["musiq"]["songQueue"][3]["externalUrl"],
            "https://open.spotify.com/track/7y6D7PitToNpVycQ2WuUPi",
        )

    def test_playlist_query(self):
        self.client.post(
            reverse("request-music"),
            {
                "query": "Myuu The Dark Piano, Vol. 3 Album",
                "playlist": "true",
                "platform": "spotify",
            },
        )
        state = self._poll_musiq_state(
            lambda state: state["musiq"]["currentSong"]
            and len(state["musiq"]["songQueue"]) == 4
            and all(song["internalUrl"] for song in state["musiq"]["songQueue"]),
            timeout=10,
        )
        self.assertEqual(
            state["musiq"]["currentSong"]["externalUrl"],
            "https://open.spotify.com/track/6nirrhTcnZClKOtMXaMJTe",
        )
        self.assertEqual(
            state["musiq"]["songQueue"][0]["externalUrl"],
            "https://open.spotify.com/track/7rGVQnTAYhrtBA5nhJrdT5",
        )
        self.assertEqual(
            state["musiq"]["songQueue"][1]["externalUrl"],
            "https://open.spotify.com/track/47u53uXlYS8JD6A4z4j8Px",
        )
        self.assertEqual(
            state["musiq"]["songQueue"][2]["externalUrl"],
            "https://open.spotify.com/track/78eYfJadYnmvJJIKCz9Rim",
        )
        self.assertEqual(
            state["musiq"]["songQueue"][3]["externalUrl"],
            "https://open.spotify.com/track/0TD7dg06fTw9ppiJvpOPAY",
        )

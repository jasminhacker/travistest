import json

from django.urls import reverse

from tests.music_test import MusicTest


class LocaldriveTests(MusicTest):
    def setUp(self) -> None:
        super().setUp()
        self._setup_test_library()

    def test_suggested_song(self) -> None:
        suggestion = json.loads(
            self.client.get(
                reverse("offline-suggestions"),
                {"term": "cambini", "playlist": "false"},
            ).content
        )[-1]
        self._request_suggestion(suggestion["key"])
        state = self._poll_musiq_state(lambda state: state["musiq"]["currentSong"])
        current_song = state["musiq"]["currentSong"]
        self.assertEqual(
            current_song["externalUrl"],
            "local_library/other/Giovanni_Giuseppe_Cambini_-_Quintet_No._2_in_D_minor,_movement_3.ogg",
        )
        self.assertAlmostEqual(current_song["duration"], 234, delta=1)
        self.assertEqual(
            current_song["artist"],
            "Soni Ventorum Woodwind Quintet",
        )
        self.assertEqual(current_song["title"], "Cambini:Quintet No 2")

    def test_suggested_playlist(self) -> None:
        state = self._add_local_playlist()
        self.assertEqual(
            state["musiq"]["currentSong"]["externalUrl"],
            "local_library/other/Giovanni_Giuseppe_Cambini_-_Quintet_No._2_in_D_minor,_movement_3.ogg",
        )
        self.assertEqual(
            state["musiq"]["songQueue"][0]["externalUrl"],
            "local_library/other/Ludwig_van_Beethoven_-_Symphonie_5_c-moll_-_3._Allegro-Fugue_only.ogg",
        )
        self.assertEqual(
            state["musiq"]["songQueue"][1]["externalUrl"],
            "local_library/other/Pietro_Mascagni_-_Cavalleria_Rusticana_-_Intermezzo_Sinfonico.ogg",
        )
        self.assertEqual(
            state["musiq"]["songQueue"][2]["externalUrl"],
            "local_library/brahms/Johannes_Brahms_-_Ungarischer_Tanz_5_g-moll.ogg",
        )
        self.assertEqual(
            state["musiq"]["songQueue"][3]["externalUrl"],
            "local_library/brahms/Johannes_Brahms_-_Ungarischer_Tanz_6_D-Dur.ogg",
        )

    def test_autoplay(self) -> None:
        suggestion = json.loads(
            self.client.get(
                reverse("offline-suggestions"),
                {"term": "cambini", "playlist": "false"},
            ).content
        )[-1]
        self.client.post(
            reverse("request-music"),
            {
                "key": suggestion["key"],
                "query": "",
                "playlist": "false",
                "platform": "local",
            },
        )
        self._poll_current_song()
        self.client.post(reverse("set-autoplay"), {"value": "true"})
        # make sure a song was downloaded into the queue
        state = self._poll_musiq_state(
            lambda state: len(state["musiq"]["songQueue"]) == 1
            and state["musiq"]["songQueue"][0]["internalUrl"]
        )
        old_id = state["musiq"]["songQueue"][0]["id"]

        self.client.post(reverse("skip"))
        self._wait_for_new_song(old_id)

    def test_radio(self) -> None:
        suggestion = json.loads(
            self.client.get(
                reverse("offline-suggestions"),
                {"term": "cambini", "playlist": "false"},
            ).content
        )[-1]
        self._request_suggestion(suggestion["key"])
        self._poll_current_song()
        self.client.post(reverse("request-radio"))
        self._poll_musiq_state(
            lambda state: len(state["musiq"]["songQueue"]) >= 1
            and all(song["internalUrl"] for song in state["musiq"]["songQueue"]),
            timeout=3,
        )

import os
import pathlib
import urllib.request
import urllib.error

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client


def admin_login(client: Client) -> None:
    user = get_user_model()
    if not user.objects.filter(username="admin").exists():
        user.objects.create_superuser("admin", "", "admin")
    client.login(username="admin", password="admin")


def download_test_library() -> bool:
    test_library = os.path.join(settings.TEST_CACHE_DIR, "test_library")
    pathlib.Path(test_library).mkdir(parents=True, exist_ok=True)
    pathlib.Path(os.path.join(test_library, "brahms")).mkdir(
        parents=True, exist_ok=True
    )
    pathlib.Path(os.path.join(test_library, "other")).mkdir(parents=True, exist_ok=True)

    brahms = [
        "Johannes_Brahms_-_Ungarischer_Tanz_5_g-moll.ogg",
        "Johannes_Brahms_-_Ungarischer_Tanz_6_D-Dur.ogg",
    ]
    other = [
        "Giovanni_Giuseppe_Cambini_-_Quintet_No._2_in_D_minor,_movement_3.ogg",
        "Pietro_Mascagni_-_Cavalleria_Rusticana_-_Intermezzo_Sinfonico.ogg",
        "Ludwig_van_Beethoven_-_Symphonie_5_c-moll_-_3._Allegro-Fugue_only.ogg",
    ]

    opener = urllib.request.build_opener()
    opener.addheaders = [
        ("User-Agent", "RaveberryTest/1.0 (contact: raveberry@jhacker.de)")
    ]
    urllib.request.install_opener(opener)

    for filename in brahms:
        target_filename = os.path.join(os.path.join(test_library, "brahms"), filename)
        if os.path.isfile(target_filename):
            continue
        try:
            urllib.request.urlretrieve(
                "https://commons.wikimedia.org/wiki/Special:Redirect/file/" + filename,
                target_filename,
            )
        except urllib.error.URLError:
            return False

    for filename in other:
        target_filename = os.path.join(os.path.join(test_library, "other"), filename)
        if os.path.isfile(target_filename):
            continue
        try:
            urllib.request.urlretrieve(
                "https://commons.wikimedia.org/wiki/Special:Redirect/file/" + filename,
                target_filename,
            )
        except urllib.error.URLError:
            return False
    return True

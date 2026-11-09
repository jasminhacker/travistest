"""Contains the core app configuration."""

import atexit
import logging
import os
import sys
import warnings

from django.apps import AppConfig

from django.conf import settings as conf
from core.util import strtobool


class CoreConfig(AppConfig):
    """This is the configuration for the core app."""

    name = "core"

    def ready(self) -> None:
        if "startcelery" in sys.argv and strtobool(os.environ.get("RUN_MAIN", "0")):
            # if the development celery process starts,
            # have it import all modules containing celery tasks
            # this way, its autoreload is notified on changes in these modules

            for module in conf.CELERY_IMPORTS:
                assert isinstance(module, str)
                __import__(module)

            return

        # ready is called for every management command and for autoreload
        # only start raveberry when
        # in debug mode and the main application is run (not autoreload)
        # or in prod mode (run by daphne)
        start_raveberry = (
            strtobool(os.environ.get("RUN_MAIN", "0"))
            if "runserver" in sys.argv
            else sys.argv[0].endswith("daphne")
        )

        if conf.TESTING:
            from core.musiq import controller

            # when MopidyAPI instances are created too often,
            # mopidy runs into a "Set changed size during iteration" error.
            # Thus we initialize the interface once and not for every testcase
            controller.start()

        if start_raveberry:
            # The warning wants to keep us from accessing the database in a not-yet-ready state
            # Since all other manage.py commands do not use the database and only here the actual
            # initialization takes place, we can silence the warning for this path
            warnings.filterwarnings(
                "ignore",
                message=r"Accessing the database during app initialization is discouraged\.",
                category=RuntimeWarning,
            )

            from core import tasks
            from core import redis
            from core.musiq import musiq
            from core.musiq import playback
            from core.settings import basic
            from core.settings import platforms

            logging.info("starting raveberry")

            redis.start()
            tasks.start()

            # platforms needs to start before musiq because mopidy_available is checked there
            platforms.start()
            musiq.start()
            basic.start()

            def stop_workers() -> None:
                # wake up the playback thread and stop it
                redis.put("stop_playback_loop", True)
                playback.queue_changed.set()

            atexit.register(stop_workers)

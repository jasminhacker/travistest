#!/usr/bin/env python

try:
    from django.core.management import execute_from_command_line

    print("django import worked")
except ImportError as exc:
    raise ImportError(
        "Couldn't import Django. Are you sure it's installed and "
        "available on your PYTHONPATH environment variable? Did you "
        "forget to activate a virtual environment?"
    ) from exc

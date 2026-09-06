"""Celery application.

Broker/result settings come from Django settings under the CELERY_ namespace
(see config/settings.py). Task modules are auto-discovered from installed apps.
"""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("fish_be")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
# core is a plain package (not in INSTALLED_APPS), so its tasks aren't picked up
# by the default app-based autodiscovery — register them explicitly.
app.autodiscover_tasks(["core.notifications"])

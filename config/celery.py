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

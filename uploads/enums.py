"""Uploads enumerations."""

from django.db import models


class ImageStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    DONE = "done", "Done"
    FAILED = "failed", "Failed"

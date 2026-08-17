"""Celery tasks for image optimization.

The task is a thin, idempotent wrapper around services.optimize_image: it takes
the PK (never a model instance), resolves the storage backend at run time, and
retries with capped exponential backoff. schedule_optimization enqueues it only
after the surrounding DB transaction commits, so the worker never races the row.
"""

from celery import shared_task
from django.db import transaction

from core.storage import get_storage
from uploads.exceptions import ImageProcessingError
from uploads.services import optimize_image

MAX_RETRIES = 3


@shared_task(bind=True, max_retries=MAX_RETRIES, name="uploads.optimize_image")
def optimize_image_task(self, image_id: int) -> None:
    try:
        optimize_image(image_id=image_id, storage=get_storage())
    except ImageProcessingError as exc:
        # Capped exponential backoff: 1s, 2s, 4s. The row is already marked
        # FAILED by the service; retries give transient errors a chance.
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


def schedule_optimization(image_id: int) -> None:
    """Enqueue optimization once the current transaction commits."""
    transaction.on_commit(lambda: optimize_image_task.delay(image_id))

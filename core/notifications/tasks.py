"""Celery task for asynchronous email delivery.

Idempotent wrapper around service.send_email: takes plain kwargs (never model
instances), and retries transient failures with capped exponential backoff.
enqueue_email schedules the send only after the surrounding DB transaction
commits, so a notification never references a row that was rolled back.
"""

from celery import shared_task
from django.db import transaction

from core.notifications.service import send_email

MAX_RETRIES = 3


@shared_task(bind=True, max_retries=MAX_RETRIES, name="notifications.send_email")
def send_email_task(
    self,
    *,
    subject: str,
    body: str,
    recipients: list[str],
    html_body: str | None = None,
) -> None:
    try:
        send_email(
            subject=subject, body=body, recipients=recipients, html_body=html_body
        )
    except Exception as exc:  # noqa: BLE001 — any delivery error is retryable
        # Capped exponential backoff: 1s, 2s, 4s.
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


def enqueue_email(
    *,
    subject: str,
    body: str,
    recipients: list[str],
    html_body: str | None = None,
) -> None:
    """Schedule an email to be sent once the current transaction commits.

    Outside a transaction, on_commit runs the callback immediately.
    """
    transaction.on_commit(
        lambda: send_email_task.delay(
            subject=subject, body=body, recipients=recipients, html_body=html_body
        )
    )

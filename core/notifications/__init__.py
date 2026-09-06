"""Email notifications: a provider-agnostic send service + async delivery task."""

from core.notifications.service import send_email
from core.notifications.tasks import enqueue_email, send_email_task

__all__ = ["send_email", "enqueue_email", "send_email_task"]

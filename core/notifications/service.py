"""Email notification service.

A thin, provider-agnostic wrapper over Django's mail layer. Callers supply an
already-rendered subject/body (each app owns the wording of its own events); this
module only knows how to deliver. Enqueuing the async send lives in tasks.py so
this module stays free of any Celery dependency.
"""

from django.conf import settings
from django.core.mail import EmailMultiAlternatives


def send_email(
    *,
    subject: str,
    body: str,
    recipients: list[str],
    html_body: str | None = None,
) -> int:
    """Send an email synchronously. Returns the number of messages delivered.

    ``recipients`` must be non-empty; an empty list is a programming error at the
    call site (missing inbox config) and should surface loudly rather than
    silently drop the notification.
    """
    if not recipients:
        raise ValueError("send_email requires at least one recipient.")

    message = EmailMultiAlternatives(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipients,
    )
    if html_body:
        message.attach_alternative(html_body, "text/html")
    return message.send()

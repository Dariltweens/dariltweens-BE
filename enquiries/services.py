"""Enquiry services.

Notifying DNL's general inbox is the one side effect, kept out of the
serializer/view so the wording lives in one place.
"""

from django.conf import settings

from core.notifications import enqueue_email
from enquiries.models import Enquiry


def notify_new_enquiry(enquiry: Enquiry) -> None:
    """Email DNL's general inbox that a contact enquiry was received."""
    body = (
        f"New contact enquiry (#{enquiry.pk}).\n\n"
        f"Name: {enquiry.name}\n"
        f"Email: {enquiry.email or '—'}\n"
        f"Phone: {enquiry.phone or '—'}\n\n"
        f"{enquiry.message}\n"
    )
    enqueue_email(
        subject=f"New contact enquiry from {enquiry.name}",
        body=body,
        recipients=[settings.DNL_GENERAL_INBOX],
    )

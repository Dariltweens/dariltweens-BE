"""Testimonial services.

The only side effect here is notifying DNL that a testimonial needs moderation.
Kept out of the serializer/view so the notification wording lives in one place.
"""

from django.conf import settings

from core.notifications import enqueue_email
from testimonials.models import Testimonial


def notify_new_testimonial(testimonial: Testimonial) -> None:
    """Email DNL's admin inbox that a testimonial is awaiting review."""
    attribution = testimonial.reviewer_name or testimonial.company_name
    body = (
        f"A new testimonial is pending review (#{testimonial.pk}).\n\n"
        f"From: {attribution}\n"
        f"Rating: {testimonial.rating or '—'}\n\n"
        f"{testimonial.body}\n"
    )
    enqueue_email(
        subject="New testimonial pending review",
        body=body,
        recipients=[settings.DNL_ADMIN_INBOX],
    )

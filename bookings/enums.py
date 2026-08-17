"""Bookings enumerations and the booking state machine.

Kept in a dependency-free leaf module so any layer can import these without
risking circular imports. ALLOWED_TRANSITIONS is not itself an enum but is the
state machine defined over BookingStatus, so it lives beside it.
"""

from django.db import models


class BookingStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    CONFIRMED = "confirmed", "Confirmed"
    CANCELLED = "cancelled", "Cancelled"
    FULFILLED = "fulfilled", "Fulfilled"


# Admin-managed state machine. Cancelled and fulfilled are terminal.
ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    BookingStatus.PENDING: {BookingStatus.CONFIRMED, BookingStatus.CANCELLED},
    BookingStatus.CONFIRMED: {BookingStatus.FULFILLED, BookingStatus.CANCELLED},
    BookingStatus.CANCELLED: set(),
    BookingStatus.FULFILLED: set(),
}

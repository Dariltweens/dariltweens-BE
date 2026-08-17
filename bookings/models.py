"""Bookings models.

A Booking reserves stock of a Product. Status is admin-managed through a small
state machine (see ALLOWED_TRANSITIONS). Stock reservation/release is handled in
services.py under a row lock to prevent overselling.
"""

from django.db import models

from bookings.enums import BookingStatus


class Booking(models.Model):
    # PROTECT: a product with bookings must not be deletable.
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.PROTECT,
        related_name="bookings",
        db_index=True,
    )
    quantity = models.PositiveIntegerField()
    pickup_date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=BookingStatus.choices,
        default=BookingStatus.PENDING,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Booking #{self.pk} ({self.status})"

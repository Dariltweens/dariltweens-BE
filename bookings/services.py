"""Booking services — the side-effecting logic lives here, not in views.

Overselling is prevented by locking the product row with select_for_update()
inside a transaction, re-checking availability, then decrementing stock and
creating the booking atomically. Status transitions run through the same locked
pattern so a cancellation reliably releases reserved stock.
"""

from datetime import date

from django.db import transaction

from bookings.enums import ALLOWED_TRANSITIONS, BookingStatus
from bookings.exceptions import InsufficientStock, InvalidTransition
from bookings.models import Booking
from catalog.models import Product


@transaction.atomic
def create_booking(*, product_id: int, quantity: int, pickup_date: date) -> Booking:
    """Reserve stock and create a pending booking, or raise.

    The product row is locked for the duration of the transaction so concurrent
    reservations serialise and cannot oversell.
    """
    if quantity <= 0:
        raise ValueError("quantity must be positive.")

    product = Product.objects.select_for_update().get(pk=product_id)
    if quantity > product.stock_quantity:
        raise InsufficientStock(
            f"Only {product.stock_quantity} in stock; requested {quantity}."
        )

    product.stock_quantity -= quantity
    product.save(update_fields=["stock_quantity", "updated_at"])

    return Booking.objects.create(
        product=product,
        quantity=quantity,
        pickup_date=pickup_date,
        status=BookingStatus.PENDING,
    )


@transaction.atomic
def transition_booking(*, booking_id: int, new_status: str) -> Booking:
    """Move a booking to ``new_status`` if the transition is allowed.

    Cancelling a non-terminal booking releases its reserved stock back to the
    product. Both the booking and its product are locked to keep the stock
    adjustment consistent under concurrency.
    """
    booking = Booking.objects.select_for_update().get(pk=booking_id)

    if new_status not in ALLOWED_TRANSITIONS.get(booking.status, set()):
        raise InvalidTransition(
            f"Cannot move booking from {booking.status} to {new_status}."
        )

    if new_status == BookingStatus.CANCELLED:
        product = Product.objects.select_for_update().get(pk=booking.product_id)
        product.stock_quantity += booking.quantity
        product.save(update_fields=["stock_quantity", "updated_at"])

    booking.status = new_status
    booking.save(update_fields=["status", "updated_at"])
    return booking

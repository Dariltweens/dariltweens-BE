"""Tests for admin-managed booking status transitions.

Transitions are validated: e.g. a cancelled booking cannot be fulfilled.
Cancelling a booking releases its reserved stock back to the product.
"""

import pytest

from datetime import timedelta

from django.utils import timezone

from bookings.enums import BookingStatus
from bookings.exceptions import InvalidTransition
from bookings.services import create_booking, transition_booking

from catalog.tests.factories import ProductFactory

PICKUP = timezone.now().date() + timedelta(days=2)

pytestmark = [pytest.mark.integration, pytest.mark.django_db]


def _make_pending(stock=10, qty=2):
    product = ProductFactory(stock_quantity=stock)
    booking = create_booking(
        product_id=product.id, quantity=qty, pickup_date=PICKUP,
        email="guest@example.com", name="Guest",
    )
    return product, booking


def test_pending_can_be_confirmed():
    _, booking = _make_pending()
    updated = transition_booking(booking_id=booking.id, new_status=BookingStatus.CONFIRMED)
    assert updated.status == BookingStatus.CONFIRMED


def test_confirmed_can_be_fulfilled():
    _, booking = _make_pending()
    transition_booking(booking_id=booking.id, new_status=BookingStatus.CONFIRMED)
    updated = transition_booking(booking_id=booking.id, new_status=BookingStatus.FULFILLED)
    assert updated.status == BookingStatus.FULFILLED


def test_cancelled_cannot_be_fulfilled():
    _, booking = _make_pending()
    transition_booking(booking_id=booking.id, new_status=BookingStatus.CANCELLED)
    with pytest.raises(InvalidTransition):
        transition_booking(booking_id=booking.id, new_status=BookingStatus.FULFILLED)


def test_fulfilled_is_terminal():
    _, booking = _make_pending()
    transition_booking(booking_id=booking.id, new_status=BookingStatus.CONFIRMED)
    transition_booking(booking_id=booking.id, new_status=BookingStatus.FULFILLED)
    with pytest.raises(InvalidTransition):
        transition_booking(booking_id=booking.id, new_status=BookingStatus.CANCELLED)


def test_cancelling_restores_reserved_stock():
    product, booking = _make_pending(stock=10, qty=3)
    product.refresh_from_db()
    assert product.stock_quantity == 7  # reserved at creation

    transition_booking(booking_id=booking.id, new_status=BookingStatus.CANCELLED)
    product.refresh_from_db()
    assert product.stock_quantity == 10  # released back


def test_fulfilling_does_not_restore_stock():
    product, booking = _make_pending(stock=10, qty=3)
    transition_booking(booking_id=booking.id, new_status=BookingStatus.CONFIRMED)
    transition_booking(booking_id=booking.id, new_status=BookingStatus.FULFILLED)
    product.refresh_from_db()
    assert product.stock_quantity == 7

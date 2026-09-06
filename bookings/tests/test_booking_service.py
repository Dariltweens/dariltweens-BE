"""Tests for booking creation — the oversell-prevention core.

Reserving stock must be atomic: lock the product row, re-check availability
inside the transaction, decrement, then create the booking. These tests prove
both the single-request logic and, via threads against real Postgres row locks,
that concurrent reservations cannot oversell.
"""

import threading
from datetime import timedelta

import pytest
from django.db import connection
from django.utils import timezone

from bookings.enums import BookingStatus
from bookings.models import Booking
from bookings.exceptions import InsufficientStock
from bookings.services import create_booking
from catalog.models import Product
from catalog.tests.factories import ProductFactory

PICKUP = timezone.now().date() + timedelta(days=2)


@pytest.mark.integration
@pytest.mark.django_db
def test_create_booking_decrements_stock_and_is_pending():
    product = ProductFactory(stock_quantity=10)
    booking = create_booking(product_id=product.id, quantity=4, pickup_date=PICKUP,
                              email="guest@example.com", name="Guest")

    product.refresh_from_db()
    assert booking.status == BookingStatus.PENDING
    assert booking.quantity == 4
    assert product.stock_quantity == 6


@pytest.mark.integration
@pytest.mark.django_db
def test_create_booking_allows_exact_remaining_stock():
    product = ProductFactory(stock_quantity=5)
    create_booking(product_id=product.id, quantity=5, pickup_date=PICKUP,
                   email="guest@example.com", name="Guest")
    product.refresh_from_db()
    assert product.stock_quantity == 0


@pytest.mark.integration
@pytest.mark.django_db
def test_create_booking_rejects_over_available_and_leaves_stock_untouched():
    product = ProductFactory(stock_quantity=3)
    with pytest.raises(InsufficientStock):
        create_booking(product_id=product.id, quantity=4, pickup_date=PICKUP,
                              email="guest@example.com", name="Guest")

    product.refresh_from_db()
    assert product.stock_quantity == 3
    assert Booking.objects.count() == 0


@pytest.mark.integration
@pytest.mark.django_db
def test_create_booking_rejects_non_positive_quantity():
    product = ProductFactory(stock_quantity=5)
    with pytest.raises(ValueError):
        create_booking(product_id=product.id, quantity=0, pickup_date=PICKUP)


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_concurrent_bookings_do_not_oversell():
    """Two threads race to book more than exists; exactly one may win."""
    product = ProductFactory(stock_quantity=1)
    barrier = threading.Barrier(2)
    results: list[str] = []

    def attempt():
        barrier.wait()  # maximise contention
        try:
            create_booking(product_id=product.id, quantity=1, pickup_date=PICKUP,
                           email="guest@example.com", name="Guest")
            results.append("ok")
        except InsufficientStock:
            results.append("rejected")
        finally:
            connection.close()  # each thread uses its own connection

    threads = [threading.Thread(target=attempt) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    product.refresh_from_db()
    assert results.count("ok") == 1
    assert results.count("rejected") == 1
    assert product.stock_quantity == 0
    assert Booking.objects.count() == 1

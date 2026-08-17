"""API tests for bookings endpoints.

Public can create a booking (which reserves stock atomically); listing and
status transitions are admin-only.
"""

from datetime import timedelta

import pytest
from django.utils import timezone

from bookings.enums import BookingStatus
from bookings.models import Booking
from catalog.tests.factories import ProductFactory

pytestmark = [pytest.mark.integration, pytest.mark.django_db]

BOOKINGS_URL = "/api/bookings/"
PICKUP = (timezone.now().date() + timedelta(days=2)).isoformat()


def test_public_can_create_booking_and_reserve_stock(api_client):
    product = ProductFactory(stock_quantity=10)
    resp = api_client.post(BOOKINGS_URL, {
        "product": product.id, "quantity": 3, "pickup_date": PICKUP,
    }, format="json")

    assert resp.status_code == 201, resp.data
    product.refresh_from_db()
    assert product.stock_quantity == 7


def test_booking_over_stock_returns_400(api_client):
    product = ProductFactory(stock_quantity=2)
    resp = api_client.post(BOOKINGS_URL, {
        "product": product.id, "quantity": 5, "pickup_date": PICKUP,
    }, format="json")
    assert resp.status_code == 400
    product.refresh_from_db()
    assert product.stock_quantity == 2


def test_public_cannot_list_bookings(api_client):
    resp = api_client.get(BOOKINGS_URL)
    assert resp.status_code in (401, 403)


def test_admin_can_list_bookings(admin_client):
    product = ProductFactory(stock_quantity=10)
    Booking.objects.create(product=product, quantity=1, pickup_date=PICKUP)
    resp = admin_client.get(BOOKINGS_URL)
    assert resp.status_code == 200
    assert resp.data["count"] == 1


def test_admin_can_transition_status(admin_client):
    product = ProductFactory(stock_quantity=10)
    booking = Booking.objects.create(product=product, quantity=1, pickup_date=PICKUP)
    resp = admin_client.patch(
        f"{BOOKINGS_URL}{booking.id}/",
        {"status": BookingStatus.CONFIRMED}, format="json",
    )
    assert resp.status_code == 200, resp.data
    booking.refresh_from_db()
    assert booking.status == BookingStatus.CONFIRMED


def test_admin_invalid_transition_returns_400(admin_client):
    product = ProductFactory(stock_quantity=10)
    booking = Booking.objects.create(product=product, quantity=1, pickup_date=PICKUP)
    resp = admin_client.patch(
        f"{BOOKINGS_URL}{booking.id}/",
        {"status": BookingStatus.FULFILLED}, format="json",  # pending->fulfilled illegal
    )
    assert resp.status_code == 400

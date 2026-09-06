"""API tests for bookings endpoints.

Public can create a booking as a guest (which reserves stock atomically and
notifies DNL); listing, notes, and status transitions are admin-only.
"""

from datetime import timedelta

import pytest
from django.core import mail
from django.utils import timezone

from bookings.enums import BookingStatus
from bookings.models import Booking
from catalog.tests.factories import ProductFactory
from customers.models import Customer
from customers.tests.factories import CustomerFactory

pytestmark = [pytest.mark.integration, pytest.mark.django_db]

BOOKINGS_URL = "/api/bookings/"
PICKUP = (timezone.now().date() + timedelta(days=2)).isoformat()
GUEST = {"name": "Ada", "email": "ada@example.com"}


def test_public_can_create_booking_and_reserve_stock(
    api_client, django_capture_on_commit_callbacks
):
    product = ProductFactory(stock_quantity=10)
    with django_capture_on_commit_callbacks(execute=True):
        resp = api_client.post(BOOKINGS_URL, {
            "product": product.id, "quantity": 3, "pickup_date": PICKUP, **GUEST,
        }, format="json")

    assert resp.status_code == 201, resp.data
    product.refresh_from_db()
    assert product.stock_quantity == 7
    # Guest was captured as a customer, and DNL was emailed.
    customer = Customer.objects.get(email="ada@example.com")
    assert Booking.objects.get().customer_id == customer.id
    assert len(mail.outbox) == 1


def test_repeat_guest_is_matched_to_existing_customer(
    api_client, django_capture_on_commit_callbacks
):
    product = ProductFactory(stock_quantity=10)
    for _ in range(2):
        with django_capture_on_commit_callbacks(execute=True):
            api_client.post(BOOKINGS_URL, {
                "product": product.id, "quantity": 1, "pickup_date": PICKUP, **GUEST,
            }, format="json")

    assert Customer.objects.filter(email="ada@example.com").count() == 1
    assert Booking.objects.count() == 2


def test_booking_requires_guest_contact(api_client):
    product = ProductFactory(stock_quantity=5)
    resp = api_client.post(BOOKINGS_URL, {
        "product": product.id, "quantity": 1, "pickup_date": PICKUP,
    }, format="json")
    assert resp.status_code == 400


def test_booking_over_stock_returns_400(api_client):
    product = ProductFactory(stock_quantity=2)
    resp = api_client.post(BOOKINGS_URL, {
        "product": product.id, "quantity": 5, "pickup_date": PICKUP, **GUEST,
    }, format="json")
    assert resp.status_code == 400
    product.refresh_from_db()
    assert product.stock_quantity == 2


def test_public_cannot_list_bookings(api_client):
    resp = api_client.get(BOOKINGS_URL)
    assert resp.status_code in (401, 403)


def test_admin_can_list_bookings(admin_client):
    product = ProductFactory(stock_quantity=10)
    Booking.objects.create(
        product=product, customer=CustomerFactory(), quantity=1, pickup_date=PICKUP
    )
    resp = admin_client.get(BOOKINGS_URL)
    assert resp.status_code == 200
    assert resp.data["count"] == 1


def test_admin_can_transition_status(admin_client):
    product = ProductFactory(stock_quantity=10)
    booking = Booking.objects.create(
        product=product, customer=CustomerFactory(), quantity=1, pickup_date=PICKUP
    )
    resp = admin_client.patch(
        f"{BOOKINGS_URL}{booking.id}/",
        {"status": BookingStatus.CONFIRMED}, format="json",
    )
    assert resp.status_code == 200, resp.data
    booking.refresh_from_db()
    assert booking.status == BookingStatus.CONFIRMED


def test_admin_can_add_notes(admin_client):
    product = ProductFactory(stock_quantity=10)
    booking = Booking.objects.create(
        product=product, customer=CustomerFactory(), quantity=1, pickup_date=PICKUP
    )
    resp = admin_client.patch(
        f"{BOOKINGS_URL}{booking.id}/",
        {"notes": "Confirmed by phone."}, format="json",
    )
    assert resp.status_code == 200, resp.data
    booking.refresh_from_db()
    assert booking.notes == "Confirmed by phone."


def test_admin_invalid_transition_returns_400(admin_client):
    product = ProductFactory(stock_quantity=10)
    booking = Booking.objects.create(
        product=product, customer=CustomerFactory(), quantity=1, pickup_date=PICKUP
    )
    resp = admin_client.patch(
        f"{BOOKINGS_URL}{booking.id}/",
        {"status": BookingStatus.FULFILLED}, format="json",  # pending->fulfilled illegal
    )
    assert resp.status_code == 400

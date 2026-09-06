"""API tests for customer auth, self-service, and admin customer list."""

from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from bookings.models import Booking
from catalog.tests.factories import ProductFactory
from customers.models import Customer
from customers.services import register_customer
from customers.tests.factories import CustomerFactory

pytestmark = [pytest.mark.integration, pytest.mark.django_db]

REGISTER_URL = "/api/auth/register/"
LOGIN_URL = "/api/auth/login/"
ME_URL = "/api/auth/me/"
CUSTOMERS_URL = "/api/customers/"
PICKUP = (timezone.now().date() + timedelta(days=2)).isoformat()


def test_public_can_register(api_client):
    resp = api_client.post(REGISTER_URL, {
        "username": "ada", "password": "s3cret-pass",
        "name": "Ada", "email": "ada@example.com",
    }, format="json")
    assert resp.status_code == 201, resp.data
    assert Customer.objects.filter(email="ada@example.com").count() == 1


def test_register_requires_a_contact(api_client):
    resp = api_client.post(REGISTER_URL, {
        "username": "ada", "password": "s3cret-pass", "name": "Ada",
    }, format="json")
    assert resp.status_code == 400


def test_login_returns_token_and_me_returns_profile(api_client):
    register_customer(
        username="ada", password="s3cret-pass", name="Ada", email="ada@example.com"
    )
    login = api_client.post(LOGIN_URL, {
        "username": "ada", "password": "s3cret-pass",
    }, format="json")
    assert login.status_code == 200, login.data
    token = login.data["access"]

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    me = client.get(ME_URL)
    assert me.status_code == 200
    assert me.data["profile"]["email"] == "ada@example.com"
    assert me.data["orders"] == []


def test_me_requires_authentication(api_client):
    resp = api_client.get(ME_URL)
    assert resp.status_code in (401, 403)


def test_logged_in_booking_attaches_to_own_customer(
    api_client, django_capture_on_commit_callbacks
):
    customer = register_customer(
        username="ada", password="s3cret-pass", name="Ada", email="ada@example.com"
    )
    product = ProductFactory(stock_quantity=10)
    api_client.force_authenticate(user=customer.user)

    with django_capture_on_commit_callbacks(execute=True):
        resp = api_client.post("/api/bookings/", {
            "product": product.id, "quantity": 2, "pickup_date": PICKUP,
        }, format="json")

    assert resp.status_code == 201, resp.data
    assert Booking.objects.get().customer_id == customer.id
    # No duplicate guest customer created.
    assert Customer.objects.count() == 1


def test_admin_can_list_customers_with_order_stats(admin_client):
    customer = CustomerFactory()
    product = ProductFactory(stock_quantity=10)
    Booking.objects.create(
        product=product, customer=customer, quantity=1, pickup_date=PICKUP
    )
    resp = admin_client.get(CUSTOMERS_URL)
    assert resp.status_code == 200
    row = resp.data["results"][0]
    assert row["total_orders"] == 1
    assert row["is_returning"] is False


def test_public_cannot_list_customers(api_client):
    resp = api_client.get(CUSTOMERS_URL)
    assert resp.status_code in (401, 403)

"""Tests for customer matching and registration services."""

import pytest

from customers.models import Customer
from customers.services import match_or_create_customer, register_customer
from customers.tests.factories import CustomerFactory

pytestmark = [pytest.mark.integration, pytest.mark.django_db]


def test_match_or_create_creates_when_no_match():
    customer, created = match_or_create_customer(
        name="Ada", email="ada@example.com", phone="+2348000000001"
    )
    assert created is True
    assert Customer.objects.count() == 1
    assert customer.name == "Ada"


def test_match_by_email_is_case_insensitive():
    existing = CustomerFactory(email="ada@example.com", phone="")
    customer, created = match_or_create_customer(name="Ada", email="ADA@example.com")
    assert created is False
    assert customer.id == existing.id


def test_match_by_phone():
    existing = CustomerFactory(email="", phone="+2348000000002")
    customer, created = match_or_create_customer(name="Ada", phone="+2348000000002")
    assert created is False
    assert customer.id == existing.id


def test_match_or_create_requires_a_contact():
    with pytest.raises(ValueError):
        match_or_create_customer(name="Ada")


def test_register_creates_user_and_links_customer():
    customer = register_customer(
        username="ada", password="s3cret-pass", name="Ada", email="ada@example.com"
    )
    assert customer.user is not None
    assert customer.user.username == "ada"
    assert customer.user.check_password("s3cret-pass")


def test_register_links_existing_guest_customer():
    guest = CustomerFactory(email="ada@example.com", phone="")
    customer = register_customer(
        username="ada", password="s3cret-pass", name="Ada", email="ada@example.com"
    )
    # The prior guest record is reused, not duplicated — history is preserved.
    assert customer.id == guest.id
    assert Customer.objects.filter(email="ada@example.com").count() == 1

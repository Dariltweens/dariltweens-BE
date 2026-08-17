"""Tests for booking serializers.

Public booking creation validates quantity at the boundary; the admin status
serializer validates that a requested transition is allowed.
"""

from datetime import timedelta

import pytest
from django.utils import timezone

from bookings.enums import BookingStatus
from bookings.serializers import BookingCreateSerializer, BookingStatusSerializer
from bookings.services import create_booking
from catalog.tests.factories import ProductFactory

PICKUP = timezone.now().date() + timedelta(days=2)

pytestmark = [pytest.mark.integration, pytest.mark.django_db]


def test_create_serializer_rejects_non_positive_quantity():
    product = ProductFactory(stock_quantity=5)
    serializer = BookingCreateSerializer(
        data={"product": product.id, "quantity": 0, "pickup_date": PICKUP}
    )
    assert not serializer.is_valid()
    assert "quantity" in serializer.errors


def test_create_serializer_rejects_past_pickup_date():
    product = ProductFactory(stock_quantity=5)
    past = timezone.now().date() - timedelta(days=1)
    serializer = BookingCreateSerializer(
        data={"product": product.id, "quantity": 1, "pickup_date": past}
    )
    assert not serializer.is_valid()
    assert "pickup_date" in serializer.errors


def test_create_serializer_valid_payload():
    product = ProductFactory(stock_quantity=5)
    serializer = BookingCreateSerializer(
        data={"product": product.id, "quantity": 2, "pickup_date": PICKUP}
    )
    assert serializer.is_valid(), serializer.errors


def test_status_serializer_rejects_invalid_transition():
    product = ProductFactory(stock_quantity=5)
    booking = create_booking(product_id=product.id, quantity=1, pickup_date=PICKUP)
    serializer = BookingStatusSerializer(
        booking, data={"status": BookingStatus.FULFILLED}, partial=True
    )
    # pending -> fulfilled is not allowed (must pass through confirmed).
    assert not serializer.is_valid()
    assert "status" in serializer.errors


def test_status_serializer_accepts_valid_transition():
    product = ProductFactory(stock_quantity=5)
    booking = create_booking(product_id=product.id, quantity=1, pickup_date=PICKUP)
    serializer = BookingStatusSerializer(
        booking, data={"status": BookingStatus.CONFIRMED}, partial=True
    )
    assert serializer.is_valid(), serializer.errors

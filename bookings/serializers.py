"""Booking serializers.

Boundary validation lives here; stock reservation and status transitions are
delegated to bookings.services so the locking/transaction logic has a single
home. BookingCreateSerializer is the public write path; BookingStatusSerializer
is the admin-only transition path.
"""

from django.utils import timezone
from rest_framework import serializers

from bookings.enums import ALLOWED_TRANSITIONS
from bookings.exceptions import InsufficientStock, InvalidTransition
from bookings.models import Booking
from bookings.services import create_booking, transition_booking


class BookingReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = [
            "id",
            "product",
            "quantity",
            "pickup_date",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class BookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ["id", "product", "quantity", "pickup_date", "status"]
        read_only_fields = ["id", "status"]

    def validate_quantity(self, value: int) -> int:
        if value <= 0:
            raise serializers.ValidationError("Quantity must be positive.")
        return value

    def validate_pickup_date(self, value):
        if value < timezone.now().date():
            raise serializers.ValidationError("Pickup date cannot be in the past.")
        return value

    def create(self, validated_data: dict) -> Booking:
        try:
            return create_booking(
                product_id=validated_data["product"].id,
                quantity=validated_data["quantity"],
                pickup_date=validated_data["pickup_date"],
            )
        except InsufficientStock as exc:
            raise serializers.ValidationError({"quantity": str(exc)}) from exc


class BookingStatusSerializer(serializers.ModelSerializer):
    """Admin-only status transitions."""

    class Meta:
        model = Booking
        fields = ["id", "status"]
        read_only_fields = ["id"]

    def validate_status(self, value: str) -> str:
        current = self.instance.status
        if value not in ALLOWED_TRANSITIONS.get(current, set()):
            raise serializers.ValidationError(
                f"Cannot move booking from {current} to {value}."
            )
        return value

    def update(self, instance: Booking, validated_data: dict) -> Booking:
        try:
            return transition_booking(
                booking_id=instance.id, new_status=validated_data["status"]
            )
        except InvalidTransition as exc:
            raise serializers.ValidationError({"status": str(exc)}) from exc

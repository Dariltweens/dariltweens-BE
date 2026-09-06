"""Booking serializers.

Boundary validation lives here; stock reservation and status transitions are
delegated to bookings.services so the locking/transaction logic has a single
home. BookingCreateSerializer is the public write path (guest or logged-in);
BookingAdminUpdateSerializer is the admin-only status/notes path.
"""

from django.utils import timezone
from rest_framework import serializers

from bookings.enums import ALLOWED_TRANSITIONS
from bookings.exceptions import InsufficientStock, InvalidTransition
from bookings.models import Booking
from bookings.services import create_booking, transition_booking


class CustomerSummarySerializer(serializers.Serializer):
    """Read-only customer snapshot nested on a booking (admin view)."""

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    email = serializers.CharField(read_only=True)
    phone = serializers.CharField(read_only=True)
    is_returning = serializers.BooleanField(read_only=True)


class BookingReadSerializer(serializers.ModelSerializer):
    customer = CustomerSummarySerializer(read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "product",
            "customer",
            "quantity",
            "pickup_date",
            "delivery_location",
            "notes",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class BookingCreateSerializer(serializers.ModelSerializer):
    # Guest contact details (write-only). Ignored when the requester is a
    # logged-in customer, whose account is used instead.
    name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    email = serializers.EmailField(write_only=True, required=False, allow_blank=True)
    phone = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "product",
            "quantity",
            "pickup_date",
            "delivery_location",
            "status",
            "name",
            "email",
            "phone",
        ]
        read_only_fields = ["id", "status"]

    def _logged_in_customer(self):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            return getattr(user, "customer", None)
        return None

    def validate_quantity(self, value: int) -> int:
        if value <= 0:
            raise serializers.ValidationError("Quantity must be positive.")
        return value

    def validate_pickup_date(self, value):
        if value < timezone.now().date():
            raise serializers.ValidationError("Pickup date cannot be in the past.")
        return value

    def validate(self, attrs: dict) -> dict:
        # Guests must supply a name plus at least one contact channel.
        if self._logged_in_customer() is None:
            if not attrs.get("name"):
                raise serializers.ValidationError({"name": "This field is required."})
            if not attrs.get("email") and not attrs.get("phone"):
                raise serializers.ValidationError(
                    "Provide an email or a phone number so DNL can reach you."
                )
        return attrs

    def create(self, validated_data: dict) -> Booking:
        customer = self._logged_in_customer()
        try:
            return create_booking(
                product_id=validated_data["product"].id,
                quantity=validated_data["quantity"],
                pickup_date=validated_data["pickup_date"],
                delivery_location=validated_data.get("delivery_location", ""),
                customer=customer,
                name=validated_data.get("name", ""),
                email=validated_data.get("email", ""),
                phone=validated_data.get("phone", ""),
            )
        except InsufficientStock as exc:
            raise serializers.ValidationError({"quantity": str(exc)}) from exc


class BookingAdminUpdateSerializer(serializers.ModelSerializer):
    """Admin-only status transitions and internal notes."""

    status = serializers.ChoiceField(
        choices=Booking._meta.get_field("status").choices, required=False
    )

    class Meta:
        model = Booking
        fields = ["id", "status", "notes"]
        read_only_fields = ["id"]

    def validate_status(self, value: str) -> str:
        current = self.instance.status
        if value != current and value not in ALLOWED_TRANSITIONS.get(current, set()):
            raise serializers.ValidationError(
                f"Cannot move booking from {current} to {value}."
            )
        return value

    def update(self, instance: Booking, validated_data: dict) -> Booking:
        new_status = validated_data.get("status")
        if new_status and new_status != instance.status:
            try:
                instance = transition_booking(
                    booking_id=instance.id, new_status=new_status
                )
            except InvalidTransition as exc:
                raise serializers.ValidationError({"status": str(exc)}) from exc
        if "notes" in validated_data:
            instance.notes = validated_data["notes"]
            instance.save(update_fields=["notes", "updated_at"])
        return instance

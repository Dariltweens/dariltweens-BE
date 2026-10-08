"""Customer serializers.

Registration delegates account+profile creation to services.register_customer.
The admin list serializer reads aggregate order stats that the view annotates onto
the queryset (so there is no per-row query in a SerializerMethodField).
"""

from rest_framework import serializers

from bookings.models import Booking
from customers.models import Customer
from customers.services import register_customer


class CustomerOrderSerializer(serializers.ModelSerializer):
    """A customer's own order — excludes admin-internal fields like notes."""

    class Meta:
        model = Booking
        fields = [
            "id",
            "product",
            "quantity",
            "pickup_date",
            "delivery_location",
            "status",
            "created_at",
        ]
        read_only_fields = fields


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=8)
    name = serializers.CharField()
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs: dict) -> dict:
        if not attrs.get("email") and not attrs.get("phone"):
            raise serializers.ValidationError("Provide an email or a phone number.")
        return attrs

    def create(self, validated_data: dict) -> Customer:
        return register_customer(
            username=validated_data["username"],
            password=validated_data["password"],
            name=validated_data["name"],
            email=validated_data.get("email", ""),
            phone=validated_data.get("phone", ""),
        )

    def to_representation(self, instance: Customer) -> dict:
        return CustomerProfileSerializer(instance).data


class CustomerProfileSerializer(serializers.ModelSerializer):
    is_returning = serializers.BooleanField(read_only=True)

    class Meta:
        model = Customer
        fields = ["id", "name", "email", "phone", "is_returning", "created_at"]
        read_only_fields = fields


class CustomerAdminSerializer(serializers.ModelSerializer):
    """Admin customer list: contact details + derived order stats."""

    is_returning = serializers.BooleanField(read_only=True)
    total_orders = serializers.IntegerField(read_only=True)
    first_order_date = serializers.DateTimeField(read_only=True)
    last_order_date = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Customer
        fields = [
            "id",
            "name",
            "email",
            "phone",
            "is_returning",
            "total_orders",
            "first_order_date",
            "last_order_date",
            "created_at",
        ]
        read_only_fields = fields

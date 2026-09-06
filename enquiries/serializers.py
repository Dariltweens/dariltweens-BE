"""Enquiry serializers.

Public create requires a reply channel and returns a confirmation (never the raw
row). The admin serializer exposes the full log and lets an admin toggle
``handled``.
"""

from rest_framework import serializers

from enquiries.models import Enquiry
from enquiries.services import notify_new_enquiry


class EnquiryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enquiry
        fields = ["id", "name", "email", "phone", "message"]
        read_only_fields = ["id"]

    def validate(self, attrs: dict) -> dict:
        if not attrs.get("email") and not attrs.get("phone"):
            raise serializers.ValidationError(
                "Provide an email or a phone number so DNL can reply."
            )
        return attrs

    def create(self, validated_data: dict) -> Enquiry:
        enquiry = Enquiry.objects.create(**validated_data)
        notify_new_enquiry(enquiry)
        return enquiry

    def to_representation(self, instance: Enquiry) -> dict:
        return {
            "id": instance.id,
            "detail": "Thank you for reaching out — DNL will be in touch shortly.",
        }


class EnquiryAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enquiry
        fields = ["id", "name", "email", "phone", "message", "handled", "created_at"]
        # Only ``handled`` is editable by the admin; the rest is the logged record.
        read_only_fields = ["id", "name", "email", "phone", "message", "created_at"]

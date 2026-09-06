"""Testimonial serializers.

Public submit (create) forces ``pending`` and requires attribution + a valid
rating; the public read serializer never exposes moderation fields. The admin
serializer exposes status and display_order for moderation and reordering.
"""

from rest_framework import serializers

from testimonials.models import Testimonial
from testimonials.services import notify_new_testimonial

MIN_RATING = 1
MAX_RATING = 5


def _validate_attribution(attrs: dict) -> None:
    if not attrs.get("reviewer_name") and not attrs.get("company_name"):
        raise serializers.ValidationError(
            "Provide your name or your company name."
        )


class TestimonialPublicSerializer(serializers.ModelSerializer):
    """Approved testimonials as shown on the site — no moderation fields."""

    class Meta:
        model = Testimonial
        fields = [
            "id",
            "reviewer_name",
            "company_name",
            "role",
            "location",
            "rating",
            "body",
            "created_at",
        ]
        read_only_fields = fields


class TestimonialCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Testimonial
        fields = [
            "id",
            "reviewer_name",
            "company_name",
            "role",
            "location",
            "rating",
            "body",
        ]
        read_only_fields = ["id"]

    def validate_rating(self, value):
        if value is not None and not (MIN_RATING <= value <= MAX_RATING):
            raise serializers.ValidationError(
                f"Rating must be between {MIN_RATING} and {MAX_RATING}."
            )
        return value

    def validate(self, attrs: dict) -> dict:
        _validate_attribution(attrs)
        return attrs

    def create(self, validated_data: dict) -> Testimonial:
        # Always pending on submit — never published straight to the site.
        testimonial = Testimonial.objects.create(**validated_data)
        notify_new_testimonial(testimonial)
        return testimonial

    def to_representation(self, instance: Testimonial) -> dict:
        return {
            "id": instance.id,
            "status": instance.status,
            "detail": "Thank you — your testimonial has been submitted for review.",
        }


class TestimonialAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Testimonial
        fields = [
            "id",
            "reviewer_name",
            "company_name",
            "role",
            "location",
            "rating",
            "body",
            "status",
            "display_order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_rating(self, value):
        if value is not None and not (MIN_RATING <= value <= MAX_RATING):
            raise serializers.ValidationError(
                f"Rating must be between {MIN_RATING} and {MAX_RATING}."
            )
        return value

    def validate(self, attrs: dict) -> dict:
        # Merge with existing instance for partial updates before checking.
        merged = {
            "reviewer_name": attrs.get(
                "reviewer_name", getattr(self.instance, "reviewer_name", "")
            ),
            "company_name": attrs.get(
                "company_name", getattr(self.instance, "company_name", "")
            ),
        }
        _validate_attribution(merged)
        return attrs

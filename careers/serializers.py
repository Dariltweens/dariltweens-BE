"""Careers serializers."""

from rest_framework import serializers

from careers.models import Job


class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = [
            "id",
            "title",
            "slug",
            "department",
            "employment_type",
            "location",
            "description",
            "requirements",
            "status",
            "created_at",
            "updated_at",
        ]
        # slug is derived from the title on save; admins never supply it.
        read_only_fields = ["id", "slug", "created_at", "updated_at"]

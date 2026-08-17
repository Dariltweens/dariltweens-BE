"""Uploads serializers.

Write path: a multipart ``image`` file is validated (DRF ImageField uses Pillow),
handed to the service which stores the original, then optimization is scheduled.
Read path: object-storage keys are turned into public URLs via the storage
manager — the model never stores URLs.
"""

from rest_framework import serializers

from core.storage import get_storage
from uploads.models import Image
from uploads.services import create_image
from uploads.tasks import schedule_optimization


class ImageSerializer(serializers.ModelSerializer):
    # Write-only multipart upload; validated as an image by DRF/Pillow.
    image = serializers.ImageField(write_only=True)
    original_url = serializers.SerializerMethodField()
    optimized_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = Image
        fields = [
            "id",
            "product",
            "image",
            "alt_text",
            "status",
            "width",
            "height",
            "original_url",
            "optimized_url",
            "thumbnail_url",
            "created_at",
        ]
        read_only_fields = [
            "id", "status", "width", "height", "created_at",
        ]

    def _url(self, key: str) -> str | None:
        return get_storage().url(key) if key else None

    def get_original_url(self, obj: Image) -> str | None:
        return self._url(obj.original_key)

    def get_optimized_url(self, obj: Image) -> str | None:
        return self._url(obj.optimized_key)

    def get_thumbnail_url(self, obj: Image) -> str | None:
        return self._url(obj.thumbnail_key)

    def create(self, validated_data: dict) -> Image:
        upload = validated_data["image"]
        image = create_image(
            product_id=validated_data["product"].id,
            file=upload,
            filename=upload.name,
            content_type=getattr(upload, "content_type", "application/octet-stream"),
            alt_text=validated_data.get("alt_text", ""),
        )
        schedule_optimization(image.id)
        return image

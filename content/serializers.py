"""Content serializers.

Write path: an optional multipart ``cover_image`` is validated (Pillow) and handed
to the service, which stores it in object storage. Read path: the stored key is
turned into a public URL via the storage manager, and read_time is derived — the
model stores neither URL nor read time.
"""

from rest_framework import serializers

from content.models import Article
from content.services import store_cover_image
from core.storage import get_storage


class ArticleSerializer(serializers.ModelSerializer):
    cover_image = serializers.ImageField(write_only=True, required=False)
    cover_image_url = serializers.SerializerMethodField()
    read_time = serializers.IntegerField(read_only=True)

    class Meta:
        model = Article
        fields = [
            "id",
            "title",
            "slug",
            "content",
            "cover_image",
            "cover_image_url",
            "read_time",
            "status",
            "published_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "published_at", "created_at", "updated_at"]

    def get_cover_image_url(self, obj: Article) -> str | None:
        return get_storage().url(obj.cover_image_key) if obj.cover_image_key else None

    def _store_cover(self, validated_data: dict) -> dict:
        upload = validated_data.pop("cover_image", None)
        if upload is not None:
            validated_data["cover_image_key"] = store_cover_image(
                file=upload,
                filename=upload.name,
                content_type=getattr(upload, "content_type", "application/octet-stream"),
            )
        return validated_data

    def create(self, validated_data: dict) -> Article:
        return super().create(self._store_cover(validated_data))

    def update(self, instance: Article, validated_data: dict) -> Article:
        return super().update(instance, self._store_cover(validated_data))

"""Content serializers."""

from rest_framework import serializers

from content.models import Article


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = [
            "id",
            "title",
            "slug",
            "content",
            "cover_image",
            "status",
            "published_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "published_at", "created_at", "updated_at"]

"""Price list serializers.

Write path: a multipart ``file`` (PDF) is validated and handed to the service,
which stores it in object storage. Read path: the stored key is turned into a
public URL via the storage manager — the model never stores URLs.
"""

from rest_framework import serializers

from core.storage import get_storage
from pricelist.models import PriceList
from pricelist.services import create_price_list

PDF_CONTENT_TYPE = "application/pdf"


class PriceListSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    uploaded_by = serializers.StringRelatedField()

    class Meta:
        model = PriceList
        fields = ["id", "filename", "content_type", "url", "uploaded_by", "uploaded_at"]
        read_only_fields = fields

    def get_url(self, obj: PriceList) -> str | None:
        return get_storage().url(obj.file_key) if obj.file_key else None


class PriceListUploadSerializer(serializers.Serializer):
    file = serializers.FileField(write_only=True)

    def validate_file(self, value):
        content_type = getattr(value, "content_type", "")
        name = getattr(value, "name", "")
        if content_type != PDF_CONTENT_TYPE and not name.lower().endswith(".pdf"):
            raise serializers.ValidationError("The price list must be a PDF file.")
        return value

    def create(self, validated_data: dict) -> PriceList:
        upload = validated_data["file"]
        request = self.context.get("request")
        return create_price_list(
            file=upload,
            filename=upload.name,
            content_type=getattr(upload, "content_type", PDF_CONTENT_TYPE),
            uploaded_by=getattr(request, "user", None),
        )

    def to_representation(self, instance: PriceList) -> dict:
        return PriceListSerializer(instance, context=self.context).data

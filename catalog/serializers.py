"""DRF serializers for the catalog app.

All input validation lives here (project convention). The critical piece is
ProductSerializer.validate_attributes, which validates a product's custom
attributes against its category's field_schema — the write-time guard that keeps
the JSONB bag honest.
"""

from rest_framework import serializers

from catalog.exceptions import SchemaError
from catalog.models import Category, Product
from catalog.services import validate_attributes, validate_field_schema


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "field_schema", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_field_schema(self, value):
        """Reject malformed schema definitions before they can be persisted."""
        try:
            validate_field_schema(value)
        except SchemaError as exc:
            raise serializers.ValidationError(str(exc)) from exc
        return value


class ProductSerializer(serializers.ModelSerializer):
    # Read: nested category. Write: category_id (PrimaryKeyRelatedField).
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        source="category",
        queryset=Category.objects.all(),
        write_only=True,
    )
    stock_status = serializers.CharField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "price",
            "category",
            "category_id",
            "attributes",
            "stock_quantity",
            "low_stock_threshold",
            "stock_status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "stock_status", "created_at", "updated_at"]

    def validate(self, attrs):
        """Validate attributes against the resolved category's schema.

        Done in validate() (not validate_attributes) because it needs both the
        category and the attributes, and on partial updates either may be absent
        from the payload — we fall back to the instance's current values.
        """
        category = attrs.get("category") or getattr(self.instance, "category", None)
        attributes = attrs.get("attributes")
        if attributes is None and self.instance is not None:
            attributes = self.instance.attributes
        if category is None:
            return attrs  # category_id is required; DRF reports that separately

        errors = validate_attributes(category.field_schema, attributes or {})
        if errors:
            raise serializers.ValidationError({"attributes": errors})
        return attrs

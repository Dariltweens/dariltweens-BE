"""DRF serializers for the catalog app.

All input validation lives here (project convention). The critical piece is
ProductSerializer.validate_attributes, which validates a product's custom
attributes against its category's field_schema — the write-time guard that keeps
the JSONB bag honest.
"""

from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample

from catalog.exceptions import SchemaError
from catalog.models import Category, Product
from catalog.services import validate_attributes, validate_field_schema


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Fish Category Schema Example",
            value={
                "name": "Fresh Fish",
                "slug": "fresh-fish",
                "field_schema": {
                    "version": 1,
                    "fields": [
                        {
                            "name": "freshness",
                            "type": "string",
                            "required": True,
                            "choices": ["fresh", "frozen"],
                        },
                        {
                            "name": "size_range",
                            "type": "string",
                            "required": False,
                            "choices": ["S", "M", "L", "XL"],
                        },
                        {
                            "name": "weight",
                            "type": "number",
                            "required": False,
                            "min": 0,
                            "max": 100,
                        },
                        {
                            "name": "wild_caught",
                            "type": "boolean",
                            "required": False,
                        },
                    ],
                },
            },
        ),
        OpenApiExample(
            "Poultry Category Schema Example",
            value={
                "name": "Poultry",
                "slug": "poultry",
                "field_schema": {
                    "version": 1,
                    "fields": [
                        {
                            "name": "breed",
                            "type": "string",
                            "required": True,
                        },
                        {
                            "name": "organic",
                            "type": "boolean",
                            "required": False,
                        },
                        {
                            "name": "weight_g",
                            "type": "number",
                            "required": True,
                            "min": 100,
                        },
                    ],
                },
            },
        ),
    ]
)
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "slug",
            "field_schema",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_field_schema(self, value):
        """Reject malformed schema definitions before they can be persisted."""
        try:
            validate_field_schema(value)
        except SchemaError as exc:
            raise serializers.ValidationError(str(exc)) from exc
        return value


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Fresh Fish Product Example",
            value={
                "name": "Atlantic Salmon",
                "description": "Premium whole fresh Atlantic Salmon.",
                "price": "24.50",
                "category_id": 1,
                "attributes": {
                    "freshness": "fresh",
                    "size_range": "L",
                    "weight": 4.2,
                    "wild_caught": True,
                },
                "stock_quantity": 45,
                "low_stock_threshold": 10,
            },
        ),
        OpenApiExample(
            "Poultry Product Example",
            value={
                "name": "Free-Range Chicken Breast",
                "description": ("Tender free-range organic chicken breast halves."),
                "price": "12.99",
                "category_id": 2,
                "attributes": {
                    "breed": "Plymouth Rock",
                    "organic": True,
                    "weight_g": 500,
                },
                "stock_quantity": 120,
                "low_stock_threshold": 20,
            },
        ),
    ]
)
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

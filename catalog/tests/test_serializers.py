"""Integration tests for ProductSerializer.

The serializer is where write-time validation lives (per project convention):
a Product's attributes must validate against its Category's field_schema, and
the read representation exposes the derived stock status and nested category.
"""

import pytest

from catalog.serializers import ProductSerializer
from catalog.tests.factories import CategoryFactory, ProductFactory

pytestmark = [pytest.mark.integration, pytest.mark.django_db]


def _payload(category, **overrides):
    data = {
        "name": "Atlantic Salmon",
        "description": "Fresh salmon",
        "price": "19.99",
        "category_id": category.id,
        "attributes": {"freshness": "fresh"},
        "stock_quantity": 10,
        "low_stock_threshold": 3,
    }
    data.update(overrides)
    return data


def test_valid_attributes_serialize_and_save():
    category = CategoryFactory()
    serializer = ProductSerializer(data=_payload(category))
    assert serializer.is_valid(), serializer.errors
    product = serializer.save()
    assert product.attributes == {"freshness": "fresh"}


def test_invalid_attributes_rejected_by_serializer():
    category = CategoryFactory()
    serializer = ProductSerializer(
        data=_payload(category, attributes={"freshness": "lukewarm"})
    )
    assert not serializer.is_valid()
    assert "attributes" in serializer.errors


def test_missing_required_attribute_rejected():
    category = CategoryFactory()
    serializer = ProductSerializer(
        data=_payload(category, attributes={"size_range": "L"})
    )
    assert not serializer.is_valid()
    assert "attributes" in serializer.errors


def test_read_representation_exposes_derived_stock_status():
    product = ProductFactory(stock_quantity=2, low_stock_threshold=5)
    data = ProductSerializer(product).data
    assert data["stock_status"] == "low_stock"
    assert data["category"]["slug"] == product.category.slug


def test_stock_status_is_read_only():
    assert ProductSerializer().fields["stock_status"].read_only

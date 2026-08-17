"""Catalog models.

The design keeps category-specific behaviour out of the schema: Category carries
a JSONB ``field_schema`` and Product carries a JSONB ``attributes`` bag. Adding a
new category is data, not a migration. Stock status is *derived*, never stored.
"""

from django.contrib.postgres.indexes import GinIndex
from django.db import models

from catalog.enums import StockStatus


class Category(models.Model):
    """A product category whose custom fields are defined by ``field_schema``."""

    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    # JSONB schema describing this category's custom fields. Validated in the
    # serializer via catalog.services.validate_field_schema.
    field_schema = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    """A product. Category-specific fields live in ``attributes`` (JSONB)."""

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    # PROTECT: a category in use must not be deletable out from under products.
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
        db_index=True,
    )
    # Custom, per-category fields validated against category.field_schema.
    attributes = models.JSONField(default=dict)
    stock_quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            # Containment / existence queries on custom attributes.
            GinIndex(fields=["attributes"], name="product_attributes_gin"),
        ]

    def __str__(self) -> str:
        return self.name

    @property
    def stock_status(self) -> str:
        """Derive stock status from quantity + threshold. Never stored."""
        if self.stock_quantity <= 0:
            return StockStatus.OUT_OF_STOCK
        if self.stock_quantity <= self.low_stock_threshold:
            return StockStatus.LOW_STOCK
        return StockStatus.IN_STOCK

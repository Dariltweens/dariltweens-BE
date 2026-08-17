"""Catalog enumerations.

Kept in a dependency-free leaf module so any layer (models, serializers,
services, tasks) can import them without risking circular imports.
"""

from django.db import models


class StockStatus(models.TextChoices):
    IN_STOCK = "in_stock", "In stock"
    LOW_STOCK = "low_stock", "Low stock"
    OUT_OF_STOCK = "out_of_stock", "Out of stock"

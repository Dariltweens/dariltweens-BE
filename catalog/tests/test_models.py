"""Integration tests for catalog models.

Focus: stock status is *derived* from quantity + threshold, never stored, and
category slug uniqueness holds at the database level.
"""

import pytest
from django.db import IntegrityError

from catalog.enums import StockStatus
from catalog.tests.factories import CategoryFactory, ProductFactory

pytestmark = [pytest.mark.integration, pytest.mark.django_db]


def test_stock_status_in_stock():
    product = ProductFactory(stock_quantity=20, low_stock_threshold=5)
    assert product.stock_status == StockStatus.IN_STOCK


def test_stock_status_low_stock_at_threshold():
    product = ProductFactory(stock_quantity=5, low_stock_threshold=5)
    assert product.stock_status == StockStatus.LOW_STOCK


def test_stock_status_low_stock_below_threshold():
    product = ProductFactory(stock_quantity=3, low_stock_threshold=5)
    assert product.stock_status == StockStatus.LOW_STOCK


def test_stock_status_out_of_stock():
    product = ProductFactory(stock_quantity=0, low_stock_threshold=5)
    assert product.stock_status == StockStatus.OUT_OF_STOCK


def test_category_slug_is_unique():
    CategoryFactory(slug="fish")
    with pytest.raises(IntegrityError):
        CategoryFactory(slug="fish")

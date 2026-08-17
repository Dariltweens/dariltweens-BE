"""API tests for the catalog endpoints.

Covers the public/admin permission split, and product filtering by category,
price range, and the *derived* stock status (the interesting one — it maps to a
comparison between two columns, not a stored field).
"""

import pytest

from catalog.tests.factories import CategoryFactory, ProductFactory

pytestmark = [pytest.mark.integration, pytest.mark.django_db]

PRODUCTS_URL = "/api/products/"
CATEGORIES_URL = "/api/categories/"


# --- permissions -----------------------------------------------------------

def test_public_can_list_products(api_client):
    ProductFactory()
    resp = api_client.get(PRODUCTS_URL)
    assert resp.status_code == 200
    assert resp.data["count"] == 1


def test_public_cannot_create_product(api_client):
    category = CategoryFactory()
    resp = api_client.post(PRODUCTS_URL, {
        "name": "X", "price": "1.00", "category_id": category.id,
        "attributes": {"freshness": "fresh"},
    }, format="json")
    assert resp.status_code in (401, 403)


def test_admin_can_create_product(admin_client):
    category = CategoryFactory()
    resp = admin_client.post(PRODUCTS_URL, {
        "name": "Salmon", "price": "9.99", "category_id": category.id,
        "attributes": {"freshness": "fresh"}, "stock_quantity": 5,
        "low_stock_threshold": 2,
    }, format="json")
    assert resp.status_code == 201, resp.data


def test_admin_create_rejects_invalid_attributes(admin_client):
    category = CategoryFactory()
    resp = admin_client.post(PRODUCTS_URL, {
        "name": "Salmon", "price": "9.99", "category_id": category.id,
        "attributes": {"freshness": "lukewarm"},
    }, format="json")
    assert resp.status_code == 400
    assert "attributes" in resp.data


def test_public_can_read_categories_but_not_write(api_client):
    CategoryFactory()
    assert api_client.get(CATEGORIES_URL).status_code == 200
    assert api_client.post(CATEGORIES_URL, {}, format="json").status_code in (401, 403)


# --- filtering -------------------------------------------------------------

def test_filter_products_by_category_slug(api_client):
    fish = CategoryFactory(slug="fish")
    poultry = CategoryFactory(slug="poultry")
    ProductFactory(category=fish)
    ProductFactory(category=poultry)

    resp = api_client.get(PRODUCTS_URL, {"category": "fish"})
    assert resp.status_code == 200
    assert resp.data["count"] == 1


def test_filter_products_by_price_range(api_client):
    ProductFactory(price="5.00")
    ProductFactory(price="15.00")
    ProductFactory(price="25.00")

    resp = api_client.get(PRODUCTS_URL, {"price_min": "10", "price_max": "20"})
    assert resp.data["count"] == 1


def test_filter_products_by_stock_status(api_client):
    ProductFactory(stock_quantity=20, low_stock_threshold=5)   # in_stock
    ProductFactory(stock_quantity=3, low_stock_threshold=5)    # low_stock
    ProductFactory(stock_quantity=0, low_stock_threshold=5)    # out_of_stock

    def count(status):
        return api_client.get(PRODUCTS_URL, {"stock_status": status}).data["count"]

    assert count("in_stock") == 1
    assert count("low_stock") == 1
    assert count("out_of_stock") == 1


def test_product_list_exposes_derived_stock_status(api_client):
    ProductFactory(stock_quantity=2, low_stock_threshold=5)
    resp = api_client.get(PRODUCTS_URL)
    assert resp.data["results"][0]["stock_status"] == "low_stock"

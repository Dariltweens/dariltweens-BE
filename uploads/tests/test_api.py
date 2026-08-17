"""API tests for image uploads.

Admins upload (multipart); the public may read image records (with URLs) but not
create them. Uploading enqueues optimization on commit.
"""

import pytest

from catalog.tests.factories import ProductFactory
from core.storage import get_storage
from uploads.enums import ImageStatus
from uploads.models import Image
from uploads.tests.helpers import make_image_upload

pytestmark = [pytest.mark.integration, pytest.mark.django_db]

IMAGES_URL = "/api/images/"


@pytest.fixture(autouse=True)
def fake_storage(settings):
    settings.STORAGE_BACKEND = "fake"
    settings.CELERY_TASK_ALWAYS_EAGER = True
    get_storage.cache_clear()
    yield
    get_storage.cache_clear()


def test_admin_can_upload_image(admin_client):
    product = ProductFactory(stock_quantity=5)
    resp = admin_client.post(IMAGES_URL, {
        "product": product.id,
        "image": make_image_upload(),
        "alt_text": "A salmon",
    }, format="multipart")

    assert resp.status_code == 201, resp.data
    assert resp.data["status"] == ImageStatus.PENDING
    image = Image.objects.get()
    assert get_storage().exists(image.original_key)


def test_public_cannot_upload_image(api_client):
    product = ProductFactory(stock_quantity=5)
    resp = api_client.post(IMAGES_URL, {
        "product": product.id, "image": make_image_upload(),
    }, format="multipart")
    assert resp.status_code in (401, 403)


def test_public_can_list_images_with_urls(api_client):
    product = ProductFactory(stock_quantity=5)
    Image.objects.create(
        product=product, original_key="k/original.png",
        optimized_key="k/optimized.webp", thumbnail_key="k/thumbnail.webp",
        content_type="image/webp", status=ImageStatus.DONE,
    )
    resp = api_client.get(IMAGES_URL)
    assert resp.status_code == 200
    assert resp.data["count"] == 1
    row = resp.data["results"][0]
    assert "optimized.webp" in row["optimized_url"]
    assert "thumbnail.webp" in row["thumbnail_url"]


def test_filter_images_by_product(api_client):
    p1 = ProductFactory(stock_quantity=5)
    p2 = ProductFactory(stock_quantity=5)
    Image.objects.create(product=p1, original_key="a", content_type="image/png",
                         status=ImageStatus.DONE)
    Image.objects.create(product=p2, original_key="b", content_type="image/png",
                         status=ImageStatus.DONE)
    resp = api_client.get(IMAGES_URL, {"product": p1.id})
    assert resp.data["count"] == 1


def test_upload_enqueues_optimization(admin_client, django_capture_on_commit_callbacks):
    product = ProductFactory(stock_quantity=5)
    with django_capture_on_commit_callbacks(execute=True) as callbacks:
        admin_client.post(IMAGES_URL, {
            "product": product.id, "image": make_image_upload(),
        }, format="multipart")

    assert len(callbacks) == 1  # optimization was scheduled on commit
    image = Image.objects.get()
    assert image.status == ImageStatus.DONE  # ran eagerly via the callback

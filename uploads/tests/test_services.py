"""Tests for the image upload + optimization pipeline.

The service depends only on the StorageClient protocol, so we inject a single
FakeStorage instance across create + optimize — no disk, no R2, no Celery.
"""

import io

import pytest

from catalog.tests.factories import ProductFactory
from core.storage import FakeStorage
from uploads.enums import ImageStatus
from uploads.exceptions import ImageProcessingError
from uploads.models import Image
from uploads.services import create_image, delete_image, optimize_image
from uploads.tests.helpers import make_image_upload

pytestmark = [pytest.mark.integration, pytest.mark.django_db]

MAX_EDGE = 1600
THUMB_EDGE = 400


def _create(storage, **kwargs):
    product = ProductFactory(stock_quantity=5)
    upload = make_image_upload(**kwargs)
    return create_image(
        product_id=product.id,
        file=upload,
        filename=upload.name,
        content_type=upload.content_type,
        storage=storage,
    )


def test_create_image_uploads_original_and_is_pending():
    storage = FakeStorage()
    image = _create(storage)

    assert image.status == ImageStatus.PENDING
    assert image.original_key
    assert storage.exists(image.original_key)
    assert not image.optimized_key


def test_optimize_produces_optimized_and_thumbnail():
    storage = FakeStorage()
    image = _create(storage)

    optimize_image(image_id=image.id, storage=storage)
    image.refresh_from_db()

    assert image.status == ImageStatus.DONE
    assert storage.exists(image.optimized_key)
    assert storage.exists(image.thumbnail_key)
    assert image.width and image.height


def test_optimize_downscales_to_max_edge():
    storage = FakeStorage()
    image = _create(storage, size=(2000, 1500))

    optimize_image(image_id=image.id, storage=storage)
    image.refresh_from_db()

    assert max(image.width, image.height) <= MAX_EDGE


def test_optimize_is_idempotent():
    storage = FakeStorage()
    image = _create(storage)

    optimize_image(image_id=image.id, storage=storage)
    first = (image.__class__.objects.get(pk=image.id).optimized_key)
    optimize_image(image_id=image.id, storage=storage)
    image.refresh_from_db()

    assert image.status == ImageStatus.DONE
    assert storage.exists(image.optimized_key)
    # Reprocessing regenerates deterministically under the same key prefix.
    assert image.optimized_key == first


def test_optimize_marks_failed_on_corrupt_original():
    storage = FakeStorage()
    product = ProductFactory(stock_quantity=5)
    # Bypass create_image: put garbage where an image should be.
    image = Image.objects.create(
        product=product, original_key="products/x/original.png",
        content_type="image/png", status=ImageStatus.PENDING,
    )
    storage.upload(io.BytesIO(b"not an image"), key=image.original_key,
                   content_type="image/png")

    with pytest.raises(ImageProcessingError):
        optimize_image(image_id=image.id, storage=storage)

    image.refresh_from_db()
    assert image.status == ImageStatus.FAILED
    assert image.error


def test_delete_image_removes_objects_and_row():
    storage = FakeStorage()
    image = _create(storage)
    optimize_image(image_id=image.id, storage=storage)
    image.refresh_from_db()
    keys = [image.original_key, image.optimized_key, image.thumbnail_key]

    delete_image(image, storage=storage)

    assert not Image.objects.filter(pk=image.id).exists()
    assert all(not storage.exists(k) for k in keys)

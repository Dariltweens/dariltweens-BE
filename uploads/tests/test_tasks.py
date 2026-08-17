"""Tests for the Celery optimization task.

Run eagerly against the shared FakeStorage singleton (resolved via get_storage),
exercising the same path a worker would take.
"""

import pytest

from catalog.tests.factories import ProductFactory
from core.storage import get_storage
from uploads.enums import ImageStatus
from uploads.services import create_image
from uploads.tasks import optimize_image_task
from uploads.tests.helpers import make_image_upload

pytestmark = [pytest.mark.integration, pytest.mark.django_db]


@pytest.fixture(autouse=True)
def fake_storage(settings):
    settings.STORAGE_BACKEND = "fake"
    get_storage.cache_clear()
    yield
    get_storage.cache_clear()


def test_task_optimizes_image_end_to_end():
    product = ProductFactory(stock_quantity=5)
    upload = make_image_upload()
    image = create_image(
        product_id=product.id, file=upload, filename=upload.name,
        content_type=upload.content_type,
    )  # uses the shared get_storage() singleton

    optimize_image_task.apply(args=[image.id]).get()
    image.refresh_from_db()

    assert image.status == ImageStatus.DONE
    assert get_storage().exists(image.optimized_key)

"""Image upload + optimization services.

These depend only on the StorageClient protocol (injected, defaulting to the
configured backend), so they are exercised in tests with FakeStorage — no R2, no
Celery. Enqueuing the async work lives in tasks.py to keep this module free of
any Celery dependency (and free of an import cycle with the task).
"""

import io
import os
import uuid
from typing import BinaryIO

from PIL import Image as PILImage

from core.storage import StorageClient, get_storage
from uploads.enums import ImageStatus
from uploads.exceptions import ImageProcessingError
from uploads.models import Image

# Optimization parameters. Long-edge caps for the two derived renditions.
MAX_EDGE = 1600
THUMB_EDGE = 400
OUTPUT_FORMAT = "WEBP"
OUTPUT_CONTENT_TYPE = "image/webp"
OUTPUT_QUALITY = 85


def _render(data: bytes, max_edge: int) -> tuple[bytes, tuple[int, int]]:
    """Downscale to fit within ``max_edge`` and re-encode as WebP."""
    img = PILImage.open(io.BytesIO(data)).convert("RGB")
    img.thumbnail((max_edge, max_edge))  # preserves aspect, only shrinks
    out = io.BytesIO()
    img.save(out, format=OUTPUT_FORMAT, quality=OUTPUT_QUALITY)
    return out.getvalue(), img.size


def create_image(
    *,
    product_id: int,
    file: BinaryIO,
    filename: str,
    content_type: str,
    alt_text: str = "",
    storage: StorageClient | None = None,
) -> Image:
    """Store the original upload and create a pending Image row.

    Fast and synchronous — the heavy optimization is scheduled separately (see
    tasks.schedule_optimization) so the request returns immediately.
    """
    storage = storage or get_storage()
    ext = os.path.splitext(filename)[1].lower() or ".bin"
    prefix = f"products/{product_id}/{uuid.uuid4().hex}"
    original_key = f"{prefix}/original{ext}"

    file.seek(0)
    storage.upload(file, key=original_key, content_type=content_type)

    return Image.objects.create(
        product_id=product_id,
        original_key=original_key,
        content_type=content_type,
        alt_text=alt_text,
        status=ImageStatus.PENDING,
    )


def optimize_image(*, image_id: int, storage: StorageClient | None = None) -> Image:
    """Generate optimized + thumbnail renditions from the stored original.

    Idempotent: derived keys are deterministic from the original key, so
    re-running overwrites in place. On failure the row is marked FAILED (with the
    error recorded) and ImageProcessingError is raised for the task to retry.
    """
    storage = storage or get_storage()
    image = Image.objects.get(pk=image_id)

    image.status = ImageStatus.PROCESSING
    image.save(update_fields=["status", "updated_at"])

    try:
        original = storage.download(image.original_key)
        optimized, (width, height) = _render(original, MAX_EDGE)
        thumbnail, _ = _render(original, THUMB_EDGE)

        prefix = image.original_key.rsplit("/", 1)[0]
        optimized_key = f"{prefix}/optimized.webp"
        thumbnail_key = f"{prefix}/thumbnail.webp"
        storage.upload(io.BytesIO(optimized), key=optimized_key,
                       content_type=OUTPUT_CONTENT_TYPE)
        storage.upload(io.BytesIO(thumbnail), key=thumbnail_key,
                       content_type=OUTPUT_CONTENT_TYPE)
    except Exception as exc:  # noqa: BLE001 — any failure marks the row FAILED
        image.status = ImageStatus.FAILED
        image.error = str(exc)
        image.save(update_fields=["status", "error", "updated_at"])
        raise ImageProcessingError(str(exc)) from exc

    image.optimized_key = optimized_key
    image.thumbnail_key = thumbnail_key
    image.width = width
    image.height = height
    image.status = ImageStatus.DONE
    image.error = ""
    image.save(update_fields=[
        "optimized_key", "thumbnail_key", "width", "height",
        "status", "error", "updated_at",
    ])
    return image


def delete_image(image: Image, *, storage: StorageClient | None = None) -> None:
    """Delete an image's stored objects, then the row."""
    storage = storage or get_storage()
    for key in (image.original_key, image.optimized_key, image.thumbnail_key):
        if key:
            storage.delete(key)
    image.delete()

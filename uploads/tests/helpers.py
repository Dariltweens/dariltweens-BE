"""Test helpers for building in-memory image uploads."""

import io

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image as PILImage


def make_image_upload(
    name: str = "test.png", size: tuple[int, int] = (2000, 1500)
) -> SimpleUploadedFile:
    buf = io.BytesIO()
    PILImage.new("RGB", size, (200, 30, 30)).save(buf, format="PNG")
    buf.seek(0)
    return SimpleUploadedFile(name, buf.read(), content_type="image/png")

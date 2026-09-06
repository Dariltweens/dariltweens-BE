"""Content services.

Cover images are stored through the core.storage manager (R2) rather than a Django
ImageField, so they survive Railway's ephemeral filesystem and stay consistent
with the uploads/pricelist apps. Depends only on the StorageClient protocol, so
it is exercised in tests with FakeStorage.
"""

import os
import uuid
from typing import BinaryIO

from core.storage import StorageClient, get_storage


def store_cover_image(
    *,
    file: BinaryIO,
    filename: str,
    content_type: str,
    storage: StorageClient | None = None,
) -> str:
    """Store an article cover image and return its storage key."""
    storage = storage or get_storage()
    ext = os.path.splitext(filename)[1].lower() or ".bin"
    key = f"articles/{uuid.uuid4().hex}{ext}"

    file.seek(0)
    storage.upload(file, key=key, content_type=content_type)
    return key

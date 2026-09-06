"""Price list services.

Storing the uploaded PDF and creating the row is a small, synchronous side effect
kept out of the serializer/view. Depends only on the StorageClient protocol so it
is exercised in tests with FakeStorage — no R2.
"""

import os
import uuid
from typing import BinaryIO

from core.storage import StorageClient, get_storage
from pricelist.models import PriceList


def create_price_list(
    *,
    file: BinaryIO,
    filename: str,
    content_type: str,
    uploaded_by=None,
    storage: StorageClient | None = None,
) -> PriceList:
    """Store the uploaded file and record it as the new current price list."""
    storage = storage or get_storage()
    ext = os.path.splitext(filename)[1].lower() or ".pdf"
    key = f"pricelists/{uuid.uuid4().hex}{ext}"

    file.seek(0)
    storage.upload(file, key=key, content_type=content_type)

    return PriceList.objects.create(
        file_key=key,
        filename=filename,
        content_type=content_type,
        uploaded_by=uploaded_by if getattr(uploaded_by, "pk", None) else None,
    )

"""Storage factory — resolves the configured StorageClient from settings.

Cached so the whole process shares one client (and, crucially, one FakeStorage
in-memory store across the request that uploads an original and the task that
reads it back). Call get_storage.cache_clear() in tests that flip the backend.
"""

from functools import lru_cache

from django.conf import settings

from core.storage.base import StorageClient
from core.storage.fake import FakeStorage
from core.storage.r2 import R2Storage


@lru_cache(maxsize=1)
def get_storage() -> StorageClient:
    backend = getattr(settings, "STORAGE_BACKEND", "fake")
    if backend == "r2":
        cfg = settings.R2_CONFIG
        return R2Storage(
            endpoint_url=cfg["ENDPOINT_URL"],
            access_key_id=cfg["ACCESS_KEY_ID"],
            secret_access_key=cfg["SECRET_ACCESS_KEY"],
            bucket=cfg["BUCKET"],
            public_base_url=cfg["PUBLIC_BASE_URL"],
        )
    return FakeStorage()

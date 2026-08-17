"""Storage abstraction: a provider-agnostic object-storage port + adapters."""

from core.storage.base import StorageClient, StorageError
from core.storage.factory import get_storage
from core.storage.fake import FakeStorage
from core.storage.r2 import R2Storage

__all__ = [
    "StorageClient",
    "StorageError",
    "get_storage",
    "FakeStorage",
    "R2Storage",
]

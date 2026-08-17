"""Storage port — the interface app code depends on.

Nothing outside core/storage/r2.py knows R2 or boto3 exists. Services accept a
StorageClient so tests can inject FakeStorage instead of the real backend.
"""

from typing import BinaryIO, Protocol, runtime_checkable


class StorageError(Exception):
    """Raised when the underlying storage backend fails an operation."""


@runtime_checkable
class StorageClient(Protocol):
    """A minimal object-storage interface (R2, S3, in-memory, ...)."""

    def upload(self, file: BinaryIO, *, key: str, content_type: str) -> str:
        """Store ``file`` under ``key``; return the stored key."""
        ...

    def download(self, key: str) -> bytes:
        """Return the bytes stored at ``key``. Raises KeyError if absent."""
        ...

    def url(self, key: str) -> str:
        """Return a publicly-servable URL for ``key``."""
        ...

    def delete(self, key: str) -> None:
        """Delete ``key``. Deleting a missing key is a no-op."""
        ...

    def exists(self, key: str) -> bool:
        """Whether an object is stored at ``key``."""
        ...

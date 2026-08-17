"""In-memory StorageClient for tests and local development.

Keeps uploaded bytes in a dict. No disk, no network — inject it wherever a
StorageClient is expected.
"""

from typing import BinaryIO


class FakeStorage:
    """In-memory implementation of the StorageClient protocol."""

    def __init__(self, base_url: str = "memory://") -> None:
        self._base_url = base_url
        self._objects: dict[str, bytes] = {}

    def upload(self, file: BinaryIO, *, key: str, content_type: str) -> str:
        self._objects[key] = file.read()
        return key

    def download(self, key: str) -> bytes:
        if key not in self._objects:
            raise KeyError(key)
        return self._objects[key]

    def url(self, key: str) -> str:
        return f"{self._base_url}{key}"

    def delete(self, key: str) -> None:
        self._objects.pop(key, None)

    def exists(self, key: str) -> bool:
        return key in self._objects

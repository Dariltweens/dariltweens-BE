"""Tests for the storage abstraction.

The pipeline depends only on the StorageClient protocol; FakeStorage is the
in-memory double we inject in tests so nothing here touches R2 or the disk.
"""

import io

import pytest

from core.storage import FakeStorage, StorageClient, get_storage

pytestmark = pytest.mark.unit


def _blob(data: bytes = b"hello") -> io.BytesIO:
    return io.BytesIO(data)


def test_fake_storage_satisfies_protocol():
    assert isinstance(FakeStorage(), StorageClient)


def test_upload_then_download_roundtrips():
    storage = FakeStorage()
    key = storage.upload(_blob(b"data"), key="a/b.txt", content_type="text/plain")
    assert key == "a/b.txt"
    assert storage.download("a/b.txt") == b"data"


def test_url_is_derived_from_key():
    storage = FakeStorage()
    storage.upload(_blob(), key="img/1.webp", content_type="image/webp")
    assert "img/1.webp" in storage.url("img/1.webp")


def test_exists_reflects_uploads_and_deletes():
    storage = FakeStorage()
    storage.upload(_blob(), key="k", content_type="text/plain")
    assert storage.exists("k")
    storage.delete("k")
    assert not storage.exists("k")


def test_download_missing_key_raises():
    with pytest.raises(KeyError):
        FakeStorage().download("nope")


def test_get_storage_returns_fake_when_configured(settings):
    settings.STORAGE_BACKEND = "fake"
    get_storage.cache_clear()
    assert isinstance(get_storage(), FakeStorage)

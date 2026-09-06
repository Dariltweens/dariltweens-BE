"""API tests for the price list.

Admins upload (multipart PDF) and list history; the public reads the current
file's metadata and downloads it without logging in. Storage is FakeStorage.
"""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from core.storage import get_storage
from pricelist.models import PriceList

pytestmark = [pytest.mark.integration, pytest.mark.django_db]

URL = "/api/price-list/"
CURRENT_URL = f"{URL}current/"
DOWNLOAD_URL = f"{URL}download/"


@pytest.fixture(autouse=True)
def fake_storage(settings):
    settings.STORAGE_BACKEND = "fake"
    get_storage.cache_clear()
    yield
    get_storage.cache_clear()


def _pdf(name="prices.pdf"):
    return SimpleUploadedFile(name, b"%PDF-1.4 fake", content_type="application/pdf")


def test_admin_can_upload_pdf(admin_client):
    resp = admin_client.post(URL, {"file": _pdf()}, format="multipart")
    assert resp.status_code == 201, resp.data
    assert resp.data["filename"] == "prices.pdf"
    price_list = PriceList.objects.get()
    assert get_storage().exists(price_list.file_key)


def test_upload_rejects_non_pdf(admin_client):
    bad = SimpleUploadedFile("prices.txt", b"nope", content_type="text/plain")
    resp = admin_client.post(URL, {"file": bad}, format="multipart")
    assert resp.status_code == 400
    assert PriceList.objects.count() == 0


def test_public_cannot_upload(api_client):
    resp = api_client.post(URL, {"file": _pdf()}, format="multipart")
    assert resp.status_code in (401, 403)


def test_public_current_returns_metadata(api_client, admin_client):
    admin_client.post(URL, {"file": _pdf()}, format="multipart")
    resp = api_client.get(CURRENT_URL)
    assert resp.status_code == 200
    assert resp.data["filename"] == "prices.pdf"
    assert resp.data["url"]
    assert resp.data["uploaded_at"]


def test_current_404_when_none(api_client):
    resp = api_client.get(CURRENT_URL)
    assert resp.status_code == 404


def test_latest_upload_becomes_current(admin_client, api_client):
    admin_client.post(URL, {"file": _pdf("old.pdf")}, format="multipart")
    admin_client.post(URL, {"file": _pdf("new.pdf")}, format="multipart")
    resp = api_client.get(CURRENT_URL)
    assert resp.data["filename"] == "new.pdf"
    assert PriceList.objects.count() == 2  # history preserved


def test_public_download_redirects(api_client, admin_client):
    admin_client.post(URL, {"file": _pdf()}, format="multipart")
    resp = api_client.get(DOWNLOAD_URL)
    assert resp.status_code == 302
    assert resp["Location"]


def test_download_404_when_none(api_client):
    resp = api_client.get(DOWNLOAD_URL)
    assert resp.status_code == 404


def test_admin_can_list_history(admin_client):
    admin_client.post(URL, {"file": _pdf("a.pdf")}, format="multipart")
    admin_client.post(URL, {"file": _pdf("b.pdf")}, format="multipart")
    resp = admin_client.get(URL)
    assert resp.status_code == 200
    assert resp.data["count"] == 2

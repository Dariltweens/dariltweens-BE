"""Tests for article cover images (stored in R2 via core.storage) and read_time."""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from content.models import Article
from content.tests.factories import ArticleFactory, PublishedArticleFactory
from core.storage import get_storage
from uploads.tests.helpers import make_image_upload

pytestmark = [pytest.mark.integration, pytest.mark.django_db]

ARTICLES_URL = "/api/articles/"


@pytest.fixture(autouse=True)
def fake_storage(settings):
    settings.STORAGE_BACKEND = "fake"
    get_storage.cache_clear()
    yield
    get_storage.cache_clear()


def test_admin_upload_cover_image_stores_key_and_exposes_url(admin_client):
    resp = admin_client.post(ARTICLES_URL, {
        "title": "With Cover", "slug": "with-cover", "content": "Body",
        "cover_image": make_image_upload(),
    }, format="multipart")

    assert resp.status_code == 201, resp.data
    assert resp.data["cover_image_url"]
    article = Article.objects.get()
    assert article.cover_image_key
    assert get_storage().exists(article.cover_image_key)


def test_cover_image_url_is_null_without_a_cover(api_client):
    PublishedArticleFactory(slug="no-cover")
    resp = api_client.get(f"{ARTICLES_URL}no-cover/")
    assert resp.status_code == 200
    assert resp.data["cover_image_url"] is None


def test_non_image_cover_is_rejected(admin_client):
    bad = SimpleUploadedFile("x.txt", b"not an image", content_type="text/plain")
    resp = admin_client.post(ARTICLES_URL, {
        "title": "Bad", "slug": "bad", "content": "Body", "cover_image": bad,
    }, format="multipart")
    assert resp.status_code == 400


def test_read_time_is_derived_from_body(api_client):
    body = " ".join(["word"] * 400)  # ~2 minutes at 200 wpm
    PublishedArticleFactory(slug="long", content=body)
    resp = api_client.get(f"{ARTICLES_URL}long/")
    assert resp.data["read_time"] == 2


def test_read_time_is_at_least_one_minute():
    article = ArticleFactory(content="short")
    assert article.read_time == 1

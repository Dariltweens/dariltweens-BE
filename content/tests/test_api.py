"""API tests for content.

The core rule: the public sees *published* articles only; drafts are invisible
to anonymous users and only admins can read or manage them.
"""

import pytest

from content.enums import ArticleStatus
from content.tests.factories import ArticleFactory, PublishedArticleFactory

pytestmark = [pytest.mark.integration, pytest.mark.django_db]

ARTICLES_URL = "/api/articles/"


# --- public visibility -----------------------------------------------------

def test_public_list_shows_published_only(api_client):
    PublishedArticleFactory()
    ArticleFactory()  # draft
    resp = api_client.get(ARTICLES_URL)
    assert resp.status_code == 200
    assert resp.data["count"] == 1


def test_public_cannot_retrieve_draft(api_client):
    draft = ArticleFactory(slug="secret")
    resp = api_client.get(f"{ARTICLES_URL}{draft.slug}/")
    assert resp.status_code == 404


def test_public_can_retrieve_published(api_client):
    article = PublishedArticleFactory(slug="live")
    resp = api_client.get(f"{ARTICLES_URL}{article.slug}/")
    assert resp.status_code == 200


def test_public_cannot_create(api_client):
    resp = api_client.post(ARTICLES_URL, {"title": "x", "content": "y"}, format="json")
    assert resp.status_code in (401, 403)


# --- admin management ------------------------------------------------------

def test_admin_sees_drafts_and_published(admin_client):
    PublishedArticleFactory()
    ArticleFactory()
    resp = admin_client.get(ARTICLES_URL)
    assert resp.status_code == 200
    assert resp.data["count"] == 2


def test_admin_can_retrieve_draft(admin_client):
    draft = ArticleFactory(slug="wip")
    resp = admin_client.get(f"{ARTICLES_URL}{draft.slug}/")
    assert resp.status_code == 200


def test_admin_can_create_article(admin_client):
    resp = admin_client.post(ARTICLES_URL, {
        "title": "News", "slug": "news", "content": "Body",
    }, format="json")
    assert resp.status_code == 201, resp.data
    assert resp.data["status"] == ArticleStatus.DRAFT


def test_admin_can_publish(admin_client):
    article = ArticleFactory(slug="draft-1")
    resp = admin_client.patch(
        f"{ARTICLES_URL}{article.slug}/",
        {"status": ArticleStatus.PUBLISHED}, format="json",
    )
    assert resp.status_code == 200, resp.data
    assert resp.data["published_at"] is not None

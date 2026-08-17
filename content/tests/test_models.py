"""Model tests for content.

An article defaults to draft; publishing stamps published_at once; slugs are
unique.
"""

import pytest
from django.db import IntegrityError

from content.enums import ArticleStatus
from content.tests.factories import ArticleFactory

pytestmark = [pytest.mark.integration, pytest.mark.django_db]


def test_article_defaults_to_draft():
    article = ArticleFactory()
    assert article.status == ArticleStatus.DRAFT
    assert article.published_at is None


def test_publishing_stamps_published_at():
    article = ArticleFactory()
    article.status = ArticleStatus.PUBLISHED
    article.save()
    article.refresh_from_db()
    assert article.published_at is not None


def test_published_at_not_overwritten_on_resave():
    article = ArticleFactory(status=ArticleStatus.PUBLISHED)
    first = article.published_at
    article.title = "Edited"
    article.save()
    article.refresh_from_db()
    assert article.published_at == first


def test_reverting_to_draft_clears_published_at():
    article = ArticleFactory(status=ArticleStatus.PUBLISHED)
    article.status = ArticleStatus.DRAFT
    article.save()
    article.refresh_from_db()
    assert article.published_at is None


def test_slug_is_unique():
    ArticleFactory(slug="hello")
    with pytest.raises(IntegrityError):
        ArticleFactory(slug="hello")

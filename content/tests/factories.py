"""factory_boy factories for content."""

import factory

from content.enums import ArticleStatus
from content.models import Article


class ArticleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Article

    title = factory.Sequence(lambda n: f"Article {n}")
    slug = factory.Sequence(lambda n: f"article-{n}")
    content = "Some body text."
    status = ArticleStatus.DRAFT


class PublishedArticleFactory(ArticleFactory):
    status = ArticleStatus.PUBLISHED

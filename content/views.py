"""Content API views.

Public reads are restricted to published articles; staff see and manage
everything. Because get_queryset itself hides drafts from the public, an
anonymous request for a draft naturally 404s rather than leaking its existence.
"""

from rest_framework import viewsets
from drf_spectacular.utils import extend_schema, extend_schema_view

from catalog.permissions import IsAdminOrReadOnly
from content.enums import ArticleStatus
from content.models import Article
from content.serializers import ArticleSerializer


@extend_schema_view(
    list=extend_schema(
        summary="List articles",
        description="Retrieve a list of articles. Public requests only see published articles, while admins see drafts as well.",
        tags=["Public - Content"],
    ),
    retrieve=extend_schema(
        summary="Retrieve an article",
        description="Retrieve detailed information about an article by slug. Anonymous or public requests can only retrieve published articles.",
        tags=["Public - Content"],
    ),
    create=extend_schema(
        summary="Create a new article",
        description="Create a new article or draft. (Admin-only)",
        tags=["Admin - Content"],
    ),
    update=extend_schema(
        summary="Update an article",
        description="Full update of an article's contents, slug, or publication status. (Admin-only)",
        tags=["Admin - Content"],
    ),
    partial_update=extend_schema(
        summary="Partially update an article",
        description="Partial update of an article. (Admin-only)",
        tags=["Admin - Content"],
    ),
    destroy=extend_schema(
        summary="Delete an article",
        description="Permanently delete an article. (Admin-only)",
        tags=["Admin - Content"],
    ),
)
class ArticleViewSet(viewsets.ModelViewSet):
    serializer_class = ArticleSerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = "slug"

    def get_queryset(self):
        qs = Article.objects.all()
        user = self.request.user
        if user and user.is_staff:
            return qs
        return qs.filter(status=ArticleStatus.PUBLISHED)

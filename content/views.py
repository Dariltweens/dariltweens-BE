"""Content API views.

Public reads are restricted to published articles; staff see and manage
everything. Because get_queryset itself hides drafts from the public, an
anonymous request for a draft naturally 404s rather than leaking its existence.
"""

from rest_framework import viewsets

from catalog.permissions import IsAdminOrReadOnly
from content.enums import ArticleStatus
from content.models import Article
from content.serializers import ArticleSerializer


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

"""Content models.

An Article moves between draft and published. published_at is stamped the first
time it becomes published and cleared if it reverts to draft, so public ordering
by publish time is reliable. That transition bookkeeping is intrinsic to the row,
so it lives in save() rather than a service.
"""

from django.db import models
from django.utils import timezone

from content.enums import ArticleStatus


class Article(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    content = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to="articles/", blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=ArticleStatus.choices,
        default=ArticleStatus.DRAFT,
        db_index=True,
    )
    published_at = models.DateTimeField(null=True, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        # Stamp published_at on first publish; clear it if reverted to draft.
        if self.status == ArticleStatus.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()
        elif self.status == ArticleStatus.DRAFT:
            self.published_at = None
        super().save(*args, **kwargs)

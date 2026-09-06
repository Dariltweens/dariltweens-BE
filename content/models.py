"""Content models.

An Article moves between draft and published. published_at is stamped the first
time it becomes published and cleared if it reverts to draft, so public ordering
by publish time is reliable. That transition bookkeeping is intrinsic to the row,
so it lives in save() rather than a service.

The cover image is stored in object storage (R2) via core.storage — the model
holds only the key (``cover_image_key``), and URLs are derived on read. read_time
is derived from the body, never stored.
"""

from django.db import models
from django.utils import timezone

from content.enums import ArticleStatus

# Average adult reading speed, used to estimate read time from the body.
WORDS_PER_MINUTE = 200


class Article(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    content = models.TextField(blank=True)
    # Object-storage key for the cover image (see core.storage); never a FileField.
    cover_image_key = models.CharField(max_length=500, blank=True)
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

    @property
    def read_time(self) -> int:
        """Estimated minutes to read the body. Derived, never stored."""
        words = len(self.content.split())
        return max(1, round(words / WORDS_PER_MINUTE))

    def save(self, *args, **kwargs):
        # Stamp published_at on first publish; clear it if reverted to draft.
        if self.status == ArticleStatus.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()
        elif self.status == ArticleStatus.DRAFT:
            self.published_at = None
        super().save(*args, **kwargs)

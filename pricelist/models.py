"""Price list models.

Each admin upload creates a new PriceList row referencing an object-storage key
(via core.storage — never a Django FileField, so this survives Railway's ephemeral
disk). History is preserved; the "current" price list is simply the most recent
row. URLs are derived on read from the storage manager, so the model stays
transport-agnostic.
"""

from django.conf import settings
from django.db import models


class PriceList(models.Model):
    file_key = models.CharField(max_length=500)
    filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100, default="application/pdf")
    # SET_NULL so a removed admin account doesn't erase the upload history.
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="price_lists",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self) -> str:
        return f"{self.filename} ({self.uploaded_at:%Y-%m-%d})"

    @classmethod
    def current(cls) -> "PriceList | None":
        """The latest uploaded price list, or None if none exists yet."""
        return cls.objects.first()

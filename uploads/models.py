"""Uploads models.

An Image row references object-storage keys (not Django ImageFields): the raw
upload lives at original_key, and the async pipeline fills optimized_key and
thumbnail_key. URLs are derived on read via the storage manager, so this model
stays transport-agnostic.
"""

from django.db import models

from uploads.enums import ImageStatus


class Image(models.Model):
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.CASCADE,  # images belong to their product
        related_name="images",
        db_index=True,
    )
    original_key = models.CharField(max_length=500)
    optimized_key = models.CharField(max_length=500, blank=True)
    thumbnail_key = models.CharField(max_length=500, blank=True)
    content_type = models.CharField(max_length=100)
    alt_text = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=20,
        choices=ImageStatus.choices,
        default=ImageStatus.PENDING,
        db_index=True,
    )
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"Image #{self.pk} ({self.status})"

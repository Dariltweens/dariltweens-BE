"""Admin for uploads."""

from django.contrib import admin

from uploads.models import Image


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ["id", "product", "status", "width", "height", "created_at"]
    list_filter = ["status"]
    search_fields = ["product__name", "alt_text"]
    autocomplete_fields = ["product"]
    list_select_related = ["product"]
    readonly_fields = [
        "original_key", "optimized_key", "thumbnail_key",
        "width", "height", "error", "created_at", "updated_at",
    ]

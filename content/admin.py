"""Admin for content."""

from django.contrib import admin

from content.models import Article


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ["title", "slug", "status", "published_at", "updated_at"]
    list_filter = ["status"]
    search_fields = ["title", "content"]
    prepopulated_fields = {"slug": ["title"]}
    readonly_fields = ["published_at", "created_at", "updated_at"]

"""Admin for content."""

from django.contrib import admin

from content.models import Article


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ["title", "slug", "status", "read_time", "published_at", "updated_at"]
    list_filter = ["status"]
    search_fields = ["title", "content"]
    prepopulated_fields = {"slug": ["title"]}
    readonly_fields = ["read_time", "published_at", "created_at", "updated_at"]

    @admin.display(description="read time (min)")
    def read_time(self, obj: Article) -> int:
        return obj.read_time

from django.contrib import admin

from careers.models import Job


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = [
        "id", "title", "department", "employment_type", "location",
        "status", "created_at",
    ]
    list_filter = ["status", "employment_type", "department"]
    search_fields = ["title", "department", "location"]
    list_editable = ["status"]
    prepopulated_fields = {"slug": ["title"]}

from django.contrib import admin

from pricelist.models import PriceList


@admin.register(PriceList)
class PriceListAdmin(admin.ModelAdmin):
    list_display = ["id", "filename", "content_type", "uploaded_by", "uploaded_at"]
    list_filter = ["uploaded_at"]
    readonly_fields = ["file_key", "uploaded_at"]

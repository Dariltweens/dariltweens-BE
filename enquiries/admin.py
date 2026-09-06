from django.contrib import admin

from enquiries.models import Enquiry


@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "email", "phone", "handled", "created_at"]
    list_filter = ["handled", "created_at"]
    search_fields = ["name", "email", "phone", "message"]
    list_editable = ["handled"]
    readonly_fields = ["name", "email", "phone", "message", "created_at"]

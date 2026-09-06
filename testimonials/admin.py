from django.contrib import admin

from testimonials.models import Testimonial


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = [
        "id", "reviewer_name", "company_name", "rating", "status",
        "display_order", "created_at",
    ]
    list_filter = ["status", "created_at"]
    search_fields = ["reviewer_name", "company_name", "body"]
    list_editable = ["status", "display_order"]

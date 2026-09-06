from django.contrib import admin

from customers.models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "phone", "user", "created_at"]
    search_fields = ["name", "email", "phone"]
    list_filter = ["created_at"]

"""Admin registrations for the catalog app."""

from django.contrib import admin

from catalog.models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "field_count", "created_at"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ["name"]}
    readonly_fields = ["created_at", "updated_at"]

    @admin.display(description="fields")
    def field_count(self, obj: Category) -> int:
        return len(obj.field_schema.get("fields", []))


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "category",
        "price",
        "stock_quantity",
        "stock_status",
    ]
    list_filter = ["category"]
    search_fields = ["name", "description"]
    autocomplete_fields = ["category"]
    readonly_fields = ["stock_status", "created_at", "updated_at"]
    list_select_related = ["category"]

    @admin.display(description="stock status")
    def stock_status(self, obj: Product) -> str:
        # Derived property; surfaced read-only in the admin.
        return obj.stock_status

"""Product filtering.

Category and price map straight to columns. Stock status is *derived* (it never
exists as a stored field), so it is translated here into a queryset condition
comparing stock_quantity against low_stock_threshold with F() expressions — the
single source of truth for that logic lives in Product.stock_status; this mirrors
it for the DB. Keep the two in sync.
"""

import django_filters
from django.db.models import F, QuerySet

from catalog.enums import StockStatus
from catalog.models import Product


class ProductFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(field_name="category__slug")
    price_min = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    price_max = django_filters.NumberFilter(field_name="price", lookup_expr="lte")
    stock_status = django_filters.ChoiceFilter(
        choices=StockStatus.choices, method="filter_stock_status"
    )

    class Meta:
        model = Product
        fields = ["category", "price_min", "price_max", "stock_status"]

    def filter_stock_status(self, queryset: QuerySet, name: str, value: str) -> QuerySet:
        if value == StockStatus.OUT_OF_STOCK:
            return queryset.filter(stock_quantity__lte=0)
        if value == StockStatus.LOW_STOCK:
            return queryset.filter(
                stock_quantity__gt=0, stock_quantity__lte=F("low_stock_threshold")
            )
        if value == StockStatus.IN_STOCK:
            return queryset.filter(stock_quantity__gt=F("low_stock_threshold"))
        return queryset

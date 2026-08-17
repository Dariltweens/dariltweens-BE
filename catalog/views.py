"""Catalog API views.

Products and categories are publicly browsable (throttled) and admin-writable.
Product querysets select_related the category to avoid N+1 from the nested
category in the serializer.
"""

from rest_framework import viewsets

from catalog.filters import ProductFilter
from catalog.models import Category, Product
from catalog.permissions import IsAdminOrReadOnly
from catalog.serializers import CategorySerializer, ProductSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = "slug"


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("category").all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_class = ProductFilter

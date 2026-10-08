"""Catalog API views.

Products and categories are publicly browsable (throttled) and admin-writable.
Product querysets select_related the category to avoid N+1 from the nested
category in the serializer.
"""

from rest_framework import viewsets
from drf_spectacular.utils import extend_schema, extend_schema_view

from catalog.filters import ProductFilter
from catalog.models import Category, Product
from catalog.permissions import IsAdminOrReadOnly
from catalog.serializers import CategorySerializer, ProductSerializer


@extend_schema_view(
    list=extend_schema(
        summary="List all categories",
        description="Retrieve a list of all product categories, including their custom field schema definitions.",
        tags=["Public - Catalog"],
    ),
    retrieve=extend_schema(
        summary="Retrieve a category",
        description="Retrieve detailed information about a single product category using its slug, including its custom field schema.",
        tags=["Public - Catalog"],
    ),
    create=extend_schema(
        summary="Create a new category",
        description="Define a new product category and its dynamic field schema. The field schema defines the dynamic properties that products of this category must have. (Admin-only)",
        tags=["Admin - Catalog"],
    ),
    update=extend_schema(
        summary="Update a category",
        description="Full update of an existing product category and its schema. (Admin-only)",
        tags=["Admin - Catalog"],
    ),
    partial_update=extend_schema(
        summary="Partially update a category",
        description="Partial update of an existing product category and its schema. (Admin-only)",
        tags=["Admin - Catalog"],
    ),
    destroy=extend_schema(
        summary="Delete a category",
        description="Permanently delete a product category. (Admin-only)",
        tags=["Admin - Catalog"],
    ),
)
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = "slug"


@extend_schema_view(
    list=extend_schema(
        summary="List and filter products",
        description="Retrieve a list of products. Supports filtering by category slug, price range, and stock status (derived from stock quantity and low stock threshold).",
        tags=["Public - Catalog"],
    ),
    retrieve=extend_schema(
        summary="Retrieve a product",
        description="Retrieve detailed information about a single product, including its category, dynamic attributes, and images.",
        tags=["Public - Catalog"],
    ),
    create=extend_schema(
        summary="Create a new product",
        description="Add a new product to the catalog. Any custom fields in the `attributes` payload are dynamically validated against the target category's schema. (Admin-only)",
        tags=["Admin - Catalog"],
    ),
    update=extend_schema(
        summary="Update a product",
        description="Full update of a product. Dynamically validates attributes against the category schema. (Admin-only)",
        tags=["Admin - Catalog"],
    ),
    partial_update=extend_schema(
        summary="Partially update a product",
        description="Partial update of a product. Dynamically validates attributes against the category schema. (Admin-only)",
        tags=["Admin - Catalog"],
    ),
    destroy=extend_schema(
        summary="Delete a product",
        description="Permanently delete a product from the catalog. (Admin-only)",
        tags=["Admin - Catalog"],
    ),
)
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("category").all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_class = ProductFilter

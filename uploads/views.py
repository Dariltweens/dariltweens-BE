"""Uploads API views.

Public may read image records (with derived URLs); only staff may upload or
delete. Deletion routes through the service so the stored objects are removed
from R2 too, not just the DB row.
"""

from rest_framework import viewsets
from drf_spectacular.utils import extend_schema, extend_schema_view

from catalog.permissions import IsAdminOrReadOnly
from core.storage import get_storage
from uploads.models import Image
from uploads.serializers import ImageSerializer
from uploads.services import delete_image


@extend_schema_view(
    list=extend_schema(
        summary="List uploaded images",
        description="Retrieve a list of uploaded product and content images, including their processing status and public URLs.",
        tags=["Public - Uploads"],
    ),
    retrieve=extend_schema(
        summary="Retrieve an image record",
        description="Retrieve detailed metadata for a single image by ID.",
        tags=["Public - Uploads"],
    ),
    create=extend_schema(
        summary="Upload a new image",
        description="Upload a new image file. This initiates an asynchronous Celery task to optimize the image (resizing, format compression to WebP) before storing it in Cloud Storage. (Admin-only)",
        tags=["Admin - Uploads"],
    ),
    update=extend_schema(
        summary="Update an image record",
        description="Full update of an image's metadata and association. (Admin-only)",
        tags=["Admin - Uploads"],
    ),
    partial_update=extend_schema(
        summary="Partially update an image record",
        description="Partial update of an image's metadata. (Admin-only)",
        tags=["Admin - Uploads"],
    ),
    destroy=extend_schema(
        summary="Delete an image",
        description="Permanently delete an image. This deletes both the database record and the corresponding file in Cloud Storage. (Admin-only)",
        tags=["Admin - Uploads"],
    ),
)
class ImageViewSet(viewsets.ModelViewSet):
    queryset = Image.objects.select_related("product").all()
    serializer_class = ImageSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ["product", "status"]

    def perform_destroy(self, instance: Image) -> None:
        delete_image(instance, storage=get_storage())

"""Uploads API views.

Public may read image records (with derived URLs); only staff may upload or
delete. Deletion routes through the service so the stored objects are removed
from R2 too, not just the DB row.
"""

from rest_framework import viewsets

from catalog.permissions import IsAdminOrReadOnly
from core.storage import get_storage
from uploads.models import Image
from uploads.serializers import ImageSerializer
from uploads.services import delete_image


class ImageViewSet(viewsets.ModelViewSet):
    queryset = Image.objects.select_related("product").all()
    serializer_class = ImageSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ["product", "status"]

    def perform_destroy(self, instance: Image) -> None:
        delete_image(instance, storage=get_storage())

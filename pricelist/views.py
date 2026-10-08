"""Price list API views.

Admins upload/replace the price list and can see the upload history; the public
may read the current file's metadata and download it — no login required. The
download endpoint redirects to the object-storage URL so the file is served
directly by the CDN, not proxied through Django.
"""

from django.http import HttpResponseRedirect
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view

from core.storage import get_storage
from pricelist.models import PriceList
from pricelist.serializers import PriceListSerializer, PriceListUploadSerializer


@extend_schema_view(
    create=extend_schema(
        summary="Upload a new price list",
        description="Upload a new PDF price list. The uploaded file is stored in Cloud Storage and marked as the active price list. (Admin-only)",
        request=PriceListUploadSerializer,
        responses={201: PriceListSerializer},
        tags=["Admin - Price List"],
    ),
    list=extend_schema(
        summary="List price list upload history",
        description="Retrieve a complete history of uploaded price lists, including the user who uploaded them. (Admin-only)",
        responses={200: PriceListSerializer(many=True)},
        tags=["Admin - Price List"],
    ),
    current=extend_schema(
        summary="Get current price list metadata",
        description="Public endpoint to retrieve metadata for the currently active price list (including public URL, filename, and last-updated time).",
        responses={200: PriceListSerializer},
        tags=["Public - Price List"],
    ),
    download=extend_schema(
        summary="Download current price list PDF",
        description="Public endpoint that redirects to the active price list file in object storage (CDN) for direct downloading.",
        responses={302: None},
        tags=["Public - Price List"],
    ),
)
class PriceListViewSet(
    mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    queryset = PriceList.objects.select_related("uploaded_by").all()
    http_method_names = ["get", "post", "head", "options"]

    def get_permissions(self):
        # Public may read/download the current file; admins upload and list history.
        if self.action in ("current", "download"):
            return [AllowAny()]
        return [IsAdminUser()]

    def get_serializer_class(self):
        if self.action == "create":
            return PriceListUploadSerializer
        return PriceListSerializer

    @action(detail=False, methods=["get"])
    def current(self, request):
        """Metadata for the current price list (url, filename, last-updated)."""
        price_list = PriceList.current()
        if price_list is None:
            return Response({"detail": "No price list available yet."}, status=404)
        return Response(self.get_serializer(price_list).data)

    @action(detail=False, methods=["get"])
    def download(self, request):
        """Redirect to the current price list file in object storage."""
        price_list = PriceList.current()
        if price_list is None:
            return Response({"detail": "No price list available yet."}, status=404)
        return HttpResponseRedirect(get_storage().url(price_list.file_key))

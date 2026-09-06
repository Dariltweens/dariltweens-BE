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

from core.storage import get_storage
from pricelist.models import PriceList
from pricelist.serializers import PriceListSerializer, PriceListUploadSerializer


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

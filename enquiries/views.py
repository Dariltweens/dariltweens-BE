"""Enquiries API views.

Public may submit a contact enquiry (throttled), which is logged and emailed to
DNL. Reading the log, marking enquiries handled, and deleting them are admin-only.
There is no public read path.
"""

from rest_framework import mixins, viewsets
from rest_framework.permissions import AllowAny, IsAdminUser

from enquiries.models import Enquiry
from enquiries.serializers import EnquiryAdminSerializer, EnquiryCreateSerializer


class EnquiryViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,  # PATCH only (see http_method_names)
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Enquiry.objects.all()
    filterset_fields = ["handled"]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
        return [IsAdminUser()]

    def get_serializer_class(self):
        if self.action == "create":
            return EnquiryCreateSerializer
        return EnquiryAdminSerializer

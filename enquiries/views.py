"""Enquiries API views.

Public may submit a contact enquiry (throttled), which is logged and emailed to
DNL. Reading the log, marking enquiries handled, and deleting them are admin-only.
There is no public read path.
"""

from rest_framework import mixins, viewsets
from rest_framework.permissions import AllowAny, IsAdminUser
from drf_spectacular.utils import extend_schema, extend_schema_view

from enquiries.models import Enquiry
from enquiries.serializers import EnquiryAdminSerializer, EnquiryCreateSerializer


@extend_schema_view(
    create=extend_schema(
        summary="Submit a contact enquiry",
        description="Public endpoint to submit a contact or business enquiry. Submissions are throttled, logged, and trigger email notifications to DNL staff.",
        request=EnquiryCreateSerializer,
        responses={201: EnquiryCreateSerializer},
        tags=["Public - Enquiries"],
    ),
    list=extend_schema(
        summary="List all enquiries",
        description="Retrieve a list of all contact enquiries. Supports filtering by the `handled` boolean field. (Admin-only)",
        responses={200: EnquiryAdminSerializer(many=True)},
        tags=["Admin - Enquiries"],
    ),
    retrieve=extend_schema(
        summary="Retrieve an enquiry",
        description="Retrieve detailed information about a single contact enquiry by ID. (Admin-only)",
        responses={200: EnquiryAdminSerializer},
        tags=["Admin - Enquiries"],
    ),
    partial_update=extend_schema(
        summary="Partially update an enquiry (PATCH)",
        description="Update specific fields of an enquiry, such as marking it as resolved/handled. (Admin-only)",
        request=EnquiryAdminSerializer,
        responses={200: EnquiryAdminSerializer},
        tags=["Admin - Enquiries"],
    ),
    destroy=extend_schema(
        summary="Delete an enquiry",
        description="Permanently delete a contact enquiry record from the database. (Admin-only)",
        tags=["Admin - Enquiries"],
    ),
)
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

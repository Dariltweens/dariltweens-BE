"""Bookings API views.

Public may create a booking (reserving stock atomically via the service layer);
listing, retrieval, and status transitions are admin-only. Full replacement
(PUT) and deletion are intentionally not exposed — status changes go through the
validated state machine via PATCH.
"""

from rest_framework import mixins, viewsets
from rest_framework.permissions import AllowAny, IsAdminUser
from drf_spectacular.utils import extend_schema, extend_schema_view

from bookings.models import Booking
from bookings.serializers import (
    BookingAdminUpdateSerializer,
    BookingCreateSerializer,
    BookingReadSerializer,
)


@extend_schema_view(
    create=extend_schema(
        summary="Create a new booking",
        description="Public endpoint to submit a booking. Atomically reserves stock inside a transaction using SELECT FOR UPDATE to prevent overselling.",
        request=BookingCreateSerializer,
        responses={201: BookingReadSerializer},
        tags=["Public - Bookings"],
    ),
    list=extend_schema(
        summary="List all bookings",
        description="Retrieve a list of all customer bookings, including nested product and customer details. (Admin-only)",
        responses={200: BookingReadSerializer(many=True)},
        tags=["Admin - Bookings"],
    ),
    retrieve=extend_schema(
        summary="Retrieve a booking",
        description="Retrieve detailed information about a single booking by ID. (Admin-only)",
        responses={200: BookingReadSerializer},
        tags=["Admin - Bookings"],
    ),
    partial_update=extend_schema(
        summary="Transition booking status (PATCH)",
        description="Transition the status of a booking. Transitions are validated (e.g., PENDING -> CONFIRMED -> FULFILLED). (Admin-only)",
        request=BookingAdminUpdateSerializer,
        responses={200: BookingReadSerializer},
        tags=["Admin - Bookings"],
    ),
)
class BookingViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,  # PATCH only (see http_method_names)
    viewsets.GenericViewSet,
):
    queryset = Booking.objects.select_related("product", "customer").all()
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_permissions(self):
        # Public may only create; everything else is admin-only.
        if self.action == "create":
            return [AllowAny()]
        return [IsAdminUser()]

    def get_serializer_class(self):
        if self.action == "create":
            return BookingCreateSerializer
        if self.action == "partial_update":
            return BookingAdminUpdateSerializer
        return BookingReadSerializer

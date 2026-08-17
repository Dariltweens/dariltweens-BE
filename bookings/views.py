"""Bookings API views.

Public may create a booking (reserving stock atomically via the service layer);
listing, retrieval, and status transitions are admin-only. Full replacement
(PUT) and deletion are intentionally not exposed — status changes go through the
validated state machine via PATCH.
"""

from rest_framework import mixins, viewsets
from rest_framework.permissions import AllowAny, IsAdminUser

from bookings.models import Booking
from bookings.serializers import (
    BookingCreateSerializer,
    BookingReadSerializer,
    BookingStatusSerializer,
)


class BookingViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,  # PATCH only (see http_method_names)
    viewsets.GenericViewSet,
):
    queryset = Booking.objects.select_related("product").all()
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
            return BookingStatusSerializer
        return BookingReadSerializer

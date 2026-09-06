"""Testimonial API views.

Public may submit a testimonial (throttled) and read approved ones; everything
else — moderation, editing, reordering, deletion — is admin-only. As with
articles, get_queryset hides non-approved rows from the public so a direct
request for a pending testimonial 404s rather than leaking it.
"""

from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAdminUser

from testimonials.enums import TestimonialStatus
from testimonials.models import Testimonial
from testimonials.serializers import (
    TestimonialAdminSerializer,
    TestimonialCreateSerializer,
    TestimonialPublicSerializer,
)


class TestimonialViewSet(viewsets.ModelViewSet):
    filterset_fields = ["status"]

    def get_permissions(self):
        # Public may create and read (approved); admins manage everything else.
        if self.action in ("update", "partial_update", "destroy"):
            return [IsAdminUser()]
        return [AllowAny()]

    def _is_staff(self) -> bool:
        user = self.request.user
        return bool(user and user.is_staff)

    def get_queryset(self):
        qs = Testimonial.objects.all()
        if self._is_staff():
            return qs
        return qs.filter(status=TestimonialStatus.APPROVED)

    def get_serializer_class(self):
        if self.action == "create":
            return TestimonialCreateSerializer
        if self._is_staff():
            return TestimonialAdminSerializer
        return TestimonialPublicSerializer

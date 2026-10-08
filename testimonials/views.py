"""Testimonial API views.

Public may submit a testimonial (throttled) and read approved ones; everything
else — moderation, editing, reordering, deletion — is admin-only. As with
articles, get_queryset hides non-approved rows from the public so a direct
request for a pending testimonial 404s rather than leaking it.
"""

from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAdminUser
from drf_spectacular.utils import extend_schema, extend_schema_view

from testimonials.enums import TestimonialStatus
from testimonials.models import Testimonial
from testimonials.serializers import (
    TestimonialAdminSerializer,
    TestimonialCreateSerializer,
    TestimonialPublicSerializer,
)


@extend_schema_view(
    list=extend_schema(
        summary="List testimonials",
        description="Retrieve testimonials. Public requests return only approved testimonials using the public serializer. Administrative requests return all testimonials (including pending/rejected) with full details.",
        responses={200: TestimonialPublicSerializer(many=True)},
        tags=["Public - Testimonials"],
    ),
    retrieve=extend_schema(
        summary="Retrieve a testimonial",
        description="Retrieve a single testimonial. Public requests only see approved testimonials. (Admin-only for pending/rejected)",
        responses={200: TestimonialPublicSerializer},
        tags=["Public - Testimonials"],
    ),
    create=extend_schema(
        summary="Submit a new testimonial",
        description="Public endpoint to submit a new testimonial. New submissions default to pending status and must be approved by an admin.",
        request=TestimonialCreateSerializer,
        responses={201: TestimonialPublicSerializer},
        tags=["Public - Testimonials"],
    ),
    update=extend_schema(
        summary="Update a testimonial",
        description="Full update of an existing testimonial, including moderation status and reordering options. (Admin-only)",
        request=TestimonialAdminSerializer,
        responses={200: TestimonialAdminSerializer},
        tags=["Admin - Testimonials"],
    ),
    partial_update=extend_schema(
        summary="Partially update a testimonial",
        description="Partial update of a testimonial. Commonly used to approve, reject, or adjust the display order. (Admin-only)",
        request=TestimonialAdminSerializer,
        responses={200: TestimonialAdminSerializer},
        tags=["Admin - Testimonials"],
    ),
    destroy=extend_schema(
        summary="Delete a testimonial",
        description="Permanently delete a testimonial. (Admin-only)",
        tags=["Admin - Testimonials"],
    ),
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

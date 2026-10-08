"""Careers API views.

Public reads are restricted to published jobs; staff see and manage everything.
As with articles, get_queryset hides unpublished jobs from the public, so an
anonymous request for one 404s rather than leaking its existence. There is no
public write path — applications happen off-platform via email.
"""

from rest_framework import viewsets
from drf_spectacular.utils import extend_schema, extend_schema_view

from careers.enums import JobStatus
from careers.models import Job
from careers.serializers import JobSerializer
from catalog.permissions import IsAdminOrReadOnly


@extend_schema_view(
    list=extend_schema(
        summary="List career openings",
        description="Retrieve a list of available job openings. Public requests only see published jobs, while admins see both drafts and published jobs.",
        tags=["Public - Careers"],
    ),
    retrieve=extend_schema(
        summary="Retrieve a career opening",
        description="Retrieve detailed information about a single career opening by slug. Public requests can only retrieve published jobs.",
        tags=["Public - Careers"],
    ),
    create=extend_schema(
        summary="Create a new career opening",
        description="Create a new career opening or draft. (Admin-only)",
        tags=["Admin - Careers"],
    ),
    update=extend_schema(
        summary="Update a career opening",
        description="Full update of an existing career opening, its requirements, or its status. (Admin-only)",
        tags=["Admin - Careers"],
    ),
    partial_update=extend_schema(
        summary="Partially update a career opening",
        description="Partial update of a career opening. (Admin-only)",
        tags=["Admin - Careers"],
    ),
    destroy=extend_schema(
        summary="Delete a career opening",
        description="Permanently delete a career opening record from the database. (Admin-only)",
        tags=["Admin - Careers"],
    ),
)
class JobViewSet(viewsets.ModelViewSet):
    serializer_class = JobSerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = "slug"

    def get_queryset(self):
        qs = Job.objects.all()
        user = self.request.user
        if user and user.is_staff:
            return qs
        return qs.filter(status=JobStatus.PUBLISHED)

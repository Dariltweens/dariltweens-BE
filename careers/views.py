"""Careers API views.

Public reads are restricted to published jobs; staff see and manage everything.
As with articles, get_queryset hides unpublished jobs from the public, so an
anonymous request for one 404s rather than leaking its existence. There is no
public write path — applications happen off-platform via email.
"""

from rest_framework import viewsets

from careers.enums import JobStatus
from careers.models import Job
from careers.serializers import JobSerializer
from catalog.permissions import IsAdminOrReadOnly


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

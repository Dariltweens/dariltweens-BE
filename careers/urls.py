"""Careers API routes."""

from rest_framework.routers import DefaultRouter

from careers.views import JobViewSet

router = DefaultRouter()
router.register("jobs", JobViewSet, basename="job")

urlpatterns = router.urls

"""Uploads API routes."""

from rest_framework.routers import DefaultRouter

from uploads.views import ImageViewSet

router = DefaultRouter()
router.register("images", ImageViewSet, basename="image")

urlpatterns = router.urls

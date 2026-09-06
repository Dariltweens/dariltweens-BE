"""Testimonials API routes."""

from rest_framework.routers import DefaultRouter

from testimonials.views import TestimonialViewSet

router = DefaultRouter()
router.register("testimonials", TestimonialViewSet, basename="testimonial")

urlpatterns = router.urls

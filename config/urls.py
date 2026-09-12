"""URL configuration for the fish_be project."""

from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health_check(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("api/health/", health_check, name="health-check"),
    path("admin/", admin.site.urls),
    path("api/", include("catalog.urls")),
    path("api/", include("bookings.urls")),
    path("api/", include("content.urls")),
    path("api/", include("uploads.urls")),
    path("api/", include("customers.urls")),
    path("api/", include("testimonials.urls")),
    path("api/", include("careers.urls")),
    path("api/", include("pricelist.urls")),
    path("api/", include("enquiries.urls")),
]

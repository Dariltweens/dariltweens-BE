"""URL configuration for the fish_be project."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
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

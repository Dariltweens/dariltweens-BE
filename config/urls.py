"""URL configuration for the fish_be project."""

from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView



def health_check(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("api/health/", health_check, name="health-check"),
    # OpenAPI
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
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

"""Customer API routes: JWT auth, self-service profile, and admin customer list."""

from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from django.urls import path

from customers.views import CustomerAdminViewSet, MeView, RegisterView

router = DefaultRouter()
router.register("customers", CustomerAdminViewSet, basename="customer")

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/login/", TokenObtainPairView.as_view(), name="auth-login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    *router.urls,
]

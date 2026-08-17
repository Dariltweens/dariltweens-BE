"""Catalog permissions."""

from rest_framework.permissions import BasePermission, IsAdminUser, SAFE_METHODS


class IsAdminOrReadOnly(BasePermission):
    """Anyone may read (throttled); only staff may write.

    Used for public-browse resources (products, categories). Reads are still
    subject to the global anon throttle configured in REST_FRAMEWORK.
    """

    def has_permission(self, request, view) -> bool:
        if request.method in SAFE_METHODS:
            return True
        return bool(IsAdminUser().has_permission(request, view))

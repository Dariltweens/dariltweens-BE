"""Shared pytest fixtures (DRF API clients)."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient


@pytest.fixture
def api_client() -> APIClient:
    """Unauthenticated client — represents the anonymous public."""
    return APIClient()


@pytest.fixture
def admin_user(db):
    User = get_user_model()
    return User.objects.create_user(
        username="admin", password="pw", is_staff=True
    )


@pytest.fixture
def admin_client(admin_user) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client

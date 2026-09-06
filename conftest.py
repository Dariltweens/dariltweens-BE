"""Shared pytest fixtures (DRF API clients)."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient


@pytest.fixture(autouse=True)
def _celery_eager_and_locmem_email(settings):
    """Run Celery tasks inline and capture email in memory for the whole suite.

    Keeps tests free of a live broker/SMTP; on_commit callbacks that enqueue a
    task execute synchronously, and sent mail lands in django.core.mail.outbox.
    """
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"


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

"""Model-level tests for careers: slug derivation and uniqueness."""

import pytest

from careers.models import Job
from careers.tests.factories import JobFactory

pytestmark = [pytest.mark.integration, pytest.mark.django_db]


def test_slug_is_derived_from_title():
    job = Job.objects.create(title="Senior Fishmonger")
    assert job.slug == "senior-fishmonger"


def test_slug_is_made_unique():
    JobFactory(title="Delivery Driver", slug="")
    second = Job.objects.create(title="Delivery Driver")
    assert second.slug == "delivery-driver-2"


def test_explicit_slug_is_respected():
    job = Job.objects.create(title="Cook", slug="head-cook")
    assert job.slug == "head-cook"

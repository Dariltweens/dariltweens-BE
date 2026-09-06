"""API tests for careers/job postings.

Public reads published jobs only; admins manage all of them. There is no public
write path — applications are handled off-platform via email.
"""

import pytest

from careers.enums import JobStatus
from careers.models import Job
from careers.tests.factories import JobFactory

pytestmark = [pytest.mark.integration, pytest.mark.django_db]

URL = "/api/jobs/"


def test_public_list_shows_published_only(api_client):
    JobFactory(status=JobStatus.PUBLISHED, title="Open Role")
    JobFactory(status=JobStatus.UNPUBLISHED, title="Hidden Role")

    resp = api_client.get(URL)
    assert resp.status_code == 200
    assert resp.data["count"] == 1
    assert resp.data["results"][0]["title"] == "Open Role"


def test_public_can_retrieve_published_by_slug(api_client):
    job = JobFactory(status=JobStatus.PUBLISHED)
    resp = api_client.get(f"{URL}{job.slug}/")
    assert resp.status_code == 200
    assert resp.data["slug"] == job.slug


def test_public_cannot_retrieve_unpublished(api_client):
    job = JobFactory(status=JobStatus.UNPUBLISHED)
    resp = api_client.get(f"{URL}{job.slug}/")
    assert resp.status_code == 404


def test_public_cannot_create(api_client):
    resp = api_client.post(URL, {"title": "Sneaky"}, format="json")
    assert resp.status_code in (401, 403)
    assert Job.objects.count() == 0


def test_admin_can_create_job(admin_client):
    resp = admin_client.post(URL, {
        "title": "Warehouse Lead",
        "department": "Logistics",
        "employment_type": "full_time",
        "location": "Lagos",
        "description": "Lead the cold-chain team.",
        "requirements": "3+ years experience.",
    }, format="json")
    assert resp.status_code == 201, resp.data
    assert resp.data["slug"] == "warehouse-lead"  # auto-derived


def test_admin_sees_unpublished(admin_client):
    JobFactory(status=JobStatus.PUBLISHED)
    JobFactory(status=JobStatus.UNPUBLISHED)
    resp = admin_client.get(URL)
    assert resp.data["count"] == 2


def test_admin_can_unpublish(admin_client):
    job = JobFactory(status=JobStatus.PUBLISHED)
    resp = admin_client.patch(
        f"{URL}{job.slug}/", {"status": JobStatus.UNPUBLISHED}, format="json"
    )
    assert resp.status_code == 200, resp.data
    job.refresh_from_db()
    assert job.status == JobStatus.UNPUBLISHED


def test_admin_can_delete(admin_client):
    job = JobFactory()
    resp = admin_client.delete(f"{URL}{job.slug}/")
    assert resp.status_code == 204
    assert Job.objects.count() == 0

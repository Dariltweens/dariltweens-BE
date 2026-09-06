"""API tests for testimonials.

Public submits (pending, throttled) and reads approved only; admins moderate,
reorder, and delete. Submitting notifies DNL by email.
"""

import pytest
from django.core import mail

from testimonials.enums import TestimonialStatus
from testimonials.models import Testimonial
from testimonials.tests.factories import TestimonialFactory

pytestmark = [pytest.mark.integration, pytest.mark.django_db]

URL = "/api/testimonials/"


def test_public_submit_is_pending_and_notifies(
    api_client, django_capture_on_commit_callbacks
):
    with django_capture_on_commit_callbacks(execute=True):
        resp = api_client.post(URL, {
            "reviewer_name": "Ada", "body": "Excellent service.", "rating": 5,
        }, format="json")

    assert resp.status_code == 201, resp.data
    assert resp.data["status"] == TestimonialStatus.PENDING
    assert "review" in resp.data["detail"].lower()
    assert Testimonial.objects.get().status == TestimonialStatus.PENDING
    assert len(mail.outbox) == 1


def test_submit_requires_name_or_company(api_client):
    resp = api_client.post(URL, {"body": "No attribution."}, format="json")
    assert resp.status_code == 400


def test_submit_rejects_out_of_range_rating(api_client):
    resp = api_client.post(URL, {
        "reviewer_name": "Ada", "body": "Nice.", "rating": 9,
    }, format="json")
    assert resp.status_code == 400


def test_public_list_shows_approved_only(api_client):
    TestimonialFactory(status=TestimonialStatus.APPROVED, reviewer_name="Shown")
    TestimonialFactory(status=TestimonialStatus.PENDING, reviewer_name="Hidden")
    TestimonialFactory(status=TestimonialStatus.REJECTED, reviewer_name="Nope")

    resp = api_client.get(URL)
    assert resp.status_code == 200
    assert resp.data["count"] == 1
    assert resp.data["results"][0]["reviewer_name"] == "Shown"
    # Moderation fields are never exposed publicly.
    assert "status" not in resp.data["results"][0]


def test_public_cannot_retrieve_pending(api_client):
    pending = TestimonialFactory(status=TestimonialStatus.PENDING)
    resp = api_client.get(f"{URL}{pending.id}/")
    assert resp.status_code == 404


def test_public_cannot_moderate(api_client):
    t = TestimonialFactory(status=TestimonialStatus.PENDING)
    resp = api_client.patch(
        f"{URL}{t.id}/", {"status": TestimonialStatus.APPROVED}, format="json"
    )
    assert resp.status_code in (401, 403)


def test_admin_can_approve(admin_client):
    t = TestimonialFactory(status=TestimonialStatus.PENDING)
    resp = admin_client.patch(
        f"{URL}{t.id}/", {"status": TestimonialStatus.APPROVED}, format="json"
    )
    assert resp.status_code == 200, resp.data
    t.refresh_from_db()
    assert t.status == TestimonialStatus.APPROVED


def test_admin_can_unpublish_by_setting_pending(admin_client):
    t = TestimonialFactory(status=TestimonialStatus.APPROVED)
    resp = admin_client.patch(
        f"{URL}{t.id}/", {"status": TestimonialStatus.PENDING}, format="json"
    )
    assert resp.status_code == 200
    t.refresh_from_db()
    assert t.status == TestimonialStatus.PENDING


def test_admin_can_reorder(admin_client):
    t = TestimonialFactory(status=TestimonialStatus.APPROVED, display_order=0)
    resp = admin_client.patch(
        f"{URL}{t.id}/", {"display_order": 5}, format="json"
    )
    assert resp.status_code == 200
    t.refresh_from_db()
    assert t.display_order == 5


def test_admin_can_list_all_and_filter_by_status(admin_client):
    TestimonialFactory(status=TestimonialStatus.APPROVED)
    TestimonialFactory(status=TestimonialStatus.PENDING)

    all_resp = admin_client.get(URL)
    assert all_resp.data["count"] == 2

    pending_resp = admin_client.get(URL, {"status": TestimonialStatus.PENDING})
    assert pending_resp.data["count"] == 1


def test_admin_can_delete(admin_client):
    t = TestimonialFactory(status=TestimonialStatus.PENDING)
    resp = admin_client.delete(f"{URL}{t.id}/")
    assert resp.status_code == 204
    assert Testimonial.objects.count() == 0

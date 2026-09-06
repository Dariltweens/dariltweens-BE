"""API tests for contact enquiries.

Public submits (throttled) — logged + emailed to DNL's general inbox; reading the
log, marking handled, and deleting are admin-only.
"""

import pytest
from django.core import mail

from enquiries.models import Enquiry

pytestmark = [pytest.mark.integration, pytest.mark.django_db]

URL = "/api/enquiries/"
VALID = {"name": "Ada", "email": "ada@example.com", "message": "Do you deliver?"}


def test_public_submit_logs_and_notifies(
    api_client, django_capture_on_commit_callbacks
):
    with django_capture_on_commit_callbacks(execute=True):
        resp = api_client.post(URL, VALID, format="json")

    assert resp.status_code == 201, resp.data
    assert "detail" in resp.data
    assert Enquiry.objects.count() == 1
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["info@dnl.local"]  # DNL_GENERAL_INBOX default


def test_submit_requires_a_reply_channel(api_client):
    resp = api_client.post(
        URL, {"name": "Ada", "message": "No contact info."}, format="json"
    )
    assert resp.status_code == 400
    assert Enquiry.objects.count() == 0


def test_submit_accepts_phone_only(api_client, django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=True):
        resp = api_client.post(URL, {
            "name": "Ada", "phone": "+2348000000000", "message": "Call me.",
        }, format="json")
    assert resp.status_code == 201, resp.data


def test_public_cannot_list(api_client):
    resp = api_client.get(URL)
    assert resp.status_code in (401, 403)


def test_admin_can_list_and_filter_by_handled(admin_client):
    Enquiry.objects.create(name="A", email="a@x.com", message="m", handled=False)
    Enquiry.objects.create(name="B", email="b@x.com", message="m", handled=True)

    all_resp = admin_client.get(URL)
    assert all_resp.data["count"] == 2

    handled_resp = admin_client.get(URL, {"handled": "true"})
    assert handled_resp.data["count"] == 1


def test_admin_can_mark_handled(admin_client):
    enquiry = Enquiry.objects.create(name="A", email="a@x.com", message="m")
    resp = admin_client.patch(
        f"{URL}{enquiry.id}/", {"handled": True}, format="json"
    )
    assert resp.status_code == 200, resp.data
    enquiry.refresh_from_db()
    assert enquiry.handled is True


def test_admin_cannot_edit_logged_message(admin_client):
    enquiry = Enquiry.objects.create(name="A", email="a@x.com", message="original")
    admin_client.patch(f"{URL}{enquiry.id}/", {"message": "tampered"}, format="json")
    enquiry.refresh_from_db()
    assert enquiry.message == "original"  # message is read-only


def test_admin_can_delete(admin_client):
    enquiry = Enquiry.objects.create(name="A", email="a@x.com", message="m")
    resp = admin_client.delete(f"{URL}{enquiry.id}/")
    assert resp.status_code == 204
    assert Enquiry.objects.count() == 0

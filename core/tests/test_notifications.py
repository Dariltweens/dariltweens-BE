"""Tests for the email notification service and async task."""

from unittest import mock

import pytest
from celery.exceptions import Retry

from core.notifications import enqueue_email, send_email, send_email_task

pytestmark = pytest.mark.unit


def test_send_email_delivers_with_html_alternative(mailoutbox):
    send_email(
        subject="Hello",
        body="plain text",
        recipients=["dnl@example.com"],
        html_body="<p>rich</p>",
    )

    assert len(mailoutbox) == 1
    message = mailoutbox[0]
    assert message.subject == "Hello"
    assert message.to == ["dnl@example.com"]
    assert message.alternatives == [("<p>rich</p>", "text/html")]


def test_send_email_rejects_empty_recipients(mailoutbox):
    with pytest.raises(ValueError):
        send_email(subject="s", body="b", recipients=[])
    assert len(mailoutbox) == 0


def test_send_email_task_sends(mailoutbox):
    # Calling the task object runs its body synchronously with self bound.
    send_email_task(subject="Order", body="details", recipients=["orders@dnl.local"])

    assert len(mailoutbox) == 1
    assert mailoutbox[0].to == ["orders@dnl.local"]


def test_send_email_task_retries_on_failure():
    with mock.patch(
        "core.notifications.tasks.send_email", side_effect=RuntimeError("smtp down")
    ):
        with mock.patch.object(
            send_email_task, "retry", side_effect=Retry()
        ) as retry:
            with pytest.raises(Retry):
                send_email_task(subject="s", body="b", recipients=["a@b.c"])

    retry.assert_called_once()


@pytest.mark.django_db
def test_enqueue_email_schedules_on_commit(
    settings, mailoutbox, django_capture_on_commit_callbacks
):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    with django_capture_on_commit_callbacks(execute=True) as callbacks:
        enqueue_email(subject="s", body="b", recipients=["a@b.c"])

    assert len(callbacks) == 1
    assert len(mailoutbox) == 1

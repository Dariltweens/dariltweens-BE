"""Model-level tests for enquiries: the reply-channel constraint."""

import pytest
from django.db import IntegrityError

from enquiries.models import Enquiry

pytestmark = [pytest.mark.integration, pytest.mark.django_db]


def test_contact_constraint_rejects_no_channel():
    with pytest.raises(IntegrityError):
        Enquiry.objects.create(name="A", email="", phone="", message="m")


def test_phone_only_is_allowed():
    enquiry = Enquiry.objects.create(
        name="A", email="", phone="+2348000000000", message="m"
    )
    assert enquiry.pk is not None

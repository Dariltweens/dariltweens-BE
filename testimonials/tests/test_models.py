"""Model-level tests for testimonials: attribution constraint and ordering."""

import pytest
from django.db import IntegrityError

from testimonials.enums import TestimonialStatus
from testimonials.models import Testimonial
from testimonials.tests.factories import TestimonialFactory

pytestmark = [pytest.mark.integration, pytest.mark.django_db]


def test_attribution_constraint_rejects_anonymous():
    with pytest.raises(IntegrityError):
        Testimonial.objects.create(
            reviewer_name="", company_name="", body="Anonymous."
        )


def test_company_only_is_allowed():
    t = Testimonial.objects.create(
        reviewer_name="", company_name="Acme Ltd", body="Good supplier."
    )
    assert t.pk is not None


def test_default_ordering_by_display_order_then_recency():
    first = TestimonialFactory(display_order=1, status=TestimonialStatus.APPROVED)
    second = TestimonialFactory(display_order=0, status=TestimonialStatus.APPROVED)

    ordered = list(Testimonial.objects.all())
    assert ordered[0] == second  # lower display_order first
    assert ordered[1] == first

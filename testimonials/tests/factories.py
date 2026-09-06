"""factory_boy factories for testimonials."""

import factory

from testimonials.enums import TestimonialStatus
from testimonials.models import Testimonial


class TestimonialFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Testimonial

    reviewer_name = factory.Sequence(lambda n: f"Reviewer {n}")
    body = "Great, fresh fish delivered on time."
    rating = 5
    status = TestimonialStatus.PENDING

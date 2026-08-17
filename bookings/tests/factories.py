"""factory_boy factories for bookings."""

from datetime import timedelta

import factory
from django.utils import timezone

from bookings.models import Booking
from catalog.tests.factories import ProductFactory


class BookingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Booking

    product = factory.SubFactory(ProductFactory)
    quantity = 1
    pickup_date = factory.LazyFunction(lambda: timezone.now().date() + timedelta(days=2))

"""factory_boy factories for bookings."""

from datetime import timedelta

import factory
from django.utils import timezone

from bookings.models import Booking
from catalog.tests.factories import ProductFactory
from customers.tests.factories import CustomerFactory


class BookingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Booking

    product = factory.SubFactory(ProductFactory)
    customer = factory.SubFactory(CustomerFactory)
    quantity = 1
    pickup_date = factory.LazyFunction(lambda: timezone.now().date() + timedelta(days=2))

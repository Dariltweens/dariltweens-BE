"""factory_boy factories for customers."""

import factory

from customers.models import Customer


class CustomerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Customer

    name = factory.Sequence(lambda n: f"Customer {n}")
    email = factory.Sequence(lambda n: f"customer{n}@example.com")
    phone = factory.Sequence(lambda n: f"+234800000{n:04d}")

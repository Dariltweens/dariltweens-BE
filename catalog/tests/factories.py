"""factory_boy factories for catalog models."""

import factory

from catalog.models import Category, Product

FISH_SCHEMA = {
    "version": 1,
    "fields": [
        {"name": "freshness", "type": "string", "required": True,
         "choices": ["fresh", "frozen"]},
        {"name": "size_range", "type": "string", "required": False},
        {"name": "weight", "type": "number", "required": False, "min": 0, "max": 100},
    ],
}


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Sequence(lambda n: f"Category {n}")
    slug = factory.Sequence(lambda n: f"category-{n}")
    field_schema = factory.LazyFunction(lambda: dict(FISH_SCHEMA))


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product

    name = factory.Sequence(lambda n: f"Product {n}")
    description = "A fine product."
    price = factory.Faker("pydecimal", left_digits=3, right_digits=2, positive=True)
    category = factory.SubFactory(CategoryFactory)
    attributes = factory.LazyFunction(lambda: {"freshness": "fresh"})
    stock_quantity = 20
    low_stock_threshold = 5

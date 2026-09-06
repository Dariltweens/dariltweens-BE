"""factory_boy factories for careers."""

import factory

from careers.enums import JobStatus
from careers.models import Job


class JobFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Job

    title = factory.Sequence(lambda n: f"Fishmonger {n}")
    department = "Operations"
    location = "Lagos"
    description = "Handle fresh and frozen stock."
    requirements = "Attention to hygiene standards."
    status = JobStatus.PUBLISHED

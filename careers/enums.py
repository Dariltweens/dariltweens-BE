"""Careers enumerations.

Dependency-free leaf module so any layer can import without circular-import risk.
"""

from django.db import models


class JobStatus(models.TextChoices):
    PUBLISHED = "published", "Published"
    UNPUBLISHED = "unpublished", "Unpublished"


class EmploymentType(models.TextChoices):
    FULL_TIME = "full_time", "Full time"
    PART_TIME = "part_time", "Part time"
    CONTRACT = "contract", "Contract"
    INTERNSHIP = "internship", "Internship"
    TEMPORARY = "temporary", "Temporary"

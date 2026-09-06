"""Testimonial enumerations.

Dependency-free leaf module so any layer can import without circular-import risk.
"""

from django.db import models


class TestimonialStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"

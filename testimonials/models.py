"""Testimonial models.

Public submissions land as ``pending`` and only appear on the site once an admin
approves them. ``display_order`` lets an admin arrange approved testimonials;
public reads order by it (then newest first). At least one of reviewer_name /
company_name must be present — enforced in the serializer and by a constraint.
"""

from django.db import models

from testimonials.enums import TestimonialStatus


class Testimonial(models.Model):
    reviewer_name = models.CharField(max_length=200, blank=True)
    company_name = models.CharField(max_length=200, blank=True)
    role = models.CharField(max_length=200, blank=True)
    location = models.CharField(max_length=200, blank=True)
    rating = models.PositiveSmallIntegerField(null=True, blank=True)
    body = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=TestimonialStatus.choices,
        default=TestimonialStatus.PENDING,
        db_index=True,
    )
    # Admin-controlled ordering for approved testimonials.
    display_order = models.PositiveIntegerField(default=0, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "-created_at"]
        constraints = [
            # A testimonial must be attributable to a person or a company.
            models.CheckConstraint(
                condition=~(
                    models.Q(reviewer_name="") & models.Q(company_name="")
                ),
                name="testimonial_has_attribution",
            ),
        ]

    def __str__(self) -> str:
        return self.reviewer_name or self.company_name or f"Testimonial #{self.pk}"

"""Enquiries models.

Backs the public contact form: each submission is logged here (a unified inbox
alongside orders) and emailed to DNL. A submitter must leave at least one reply
channel (email or phone) — enforced in the serializer and by a constraint.
``handled`` lets an admin mark an enquiry as dealt with.
"""

from django.db import models


class Enquiry(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    message = models.TextField()
    handled = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=~(models.Q(email="") & models.Q(phone="")),
                name="enquiry_has_contact",
            ),
        ]

    def __str__(self) -> str:
        return f"Enquiry from {self.name} ({self.created_at:%Y-%m-%d})"

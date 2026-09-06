"""Customer models.

A Customer is the identity a booking belongs to. Guests have no linked auth
``user`` (the OneToOne is nullable); registered customers do. Repeat guests are
recognised by matching email/phone against existing rows (see services), so
"returning customer" works without forcing anyone to create an account. Whether a
customer is returning is *derived* from their booking count, never stored.
"""

from django.conf import settings
from django.db import models


class Customer(models.Model):
    # Nullable: guests have no account. SET_NULL so deleting a User keeps the
    # customer record (and its booking history) intact.
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="customer",
    )
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True, db_index=True)
    phone = models.CharField(max_length=32, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            # A customer must be reachable by at least one channel.
            models.CheckConstraint(
                condition=~(models.Q(email="") & models.Q(phone="")),
                name="customer_has_contact",
            ),
        ]

    def __str__(self) -> str:
        return self.name

    @property
    def is_returning(self) -> bool:
        """True once the customer has more than one booking. Derived, not stored.

        Prefer the ``total_orders`` annotation added by the admin list queryset to
        avoid a per-row query; this property is a correct fallback.
        """
        total = getattr(self, "total_orders", None)
        if total is None:
            total = self.bookings.count()
        return total > 1

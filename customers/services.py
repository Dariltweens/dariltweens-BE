"""Customer services.

Guest-order matching and account registration live here rather than in views or
serializers, because both are multi-step and side-effecting. match_or_create_customer
is the single place that decides whether a booking belongs to a returning customer.
"""

from django.contrib.auth import get_user_model
from django.db import models, transaction

from customers.models import Customer


def _normalise_email(email: str) -> str:
    return email.strip().lower()


def _normalise_phone(phone: str) -> str:
    return phone.strip()


def match_or_create_customer(
    *, name: str, email: str = "", phone: str = ""
) -> tuple[Customer, bool]:
    """Return the customer matching this email/phone, creating one if none exists.

    Matching a repeat guest to their prior record is what makes "returning
    customer" work without an account. Returns ``(customer, created)``.
    """
    email = _normalise_email(email)
    phone = _normalise_phone(phone)
    if not email and not phone:
        raise ValueError("A customer requires an email or a phone number.")

    lookup = models.Q()
    if email:
        lookup |= models.Q(email__iexact=email)
    if phone:
        lookup |= models.Q(phone=phone)

    existing = Customer.objects.filter(lookup).order_by("created_at").first()
    if existing is not None:
        return existing, False

    customer = Customer.objects.create(name=name, email=email, phone=phone)
    return customer, True


@transaction.atomic
def register_customer(
    *, username: str, password: str, name: str, email: str = "", phone: str = ""
) -> Customer:
    """Create a User and link it to a Customer (matching an existing guest record).

    A returning guest who registers keeps their prior booking history: we attach
    the new User to the matched customer rather than creating a duplicate.
    """
    User = get_user_model()
    user = User.objects.create_user(
        username=username, password=password, email=_normalise_email(email)
    )
    customer, _created = match_or_create_customer(name=name, email=email, phone=phone)
    customer.user = user
    if name:
        customer.name = name
    customer.save(update_fields=["user", "name", "updated_at"])
    return customer

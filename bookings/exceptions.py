"""Bookings domain exceptions.

Dependency-free leaf module so any layer can import and raise/catch these
without risking circular imports.
"""


class InsufficientStock(Exception):
    """Raised when a booking would reserve more stock than is available."""


class InvalidTransition(Exception):
    """Raised when a booking status change is not permitted."""

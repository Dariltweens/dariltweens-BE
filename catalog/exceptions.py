"""Catalog domain exceptions.

Dependency-free leaf module so any layer can import and raise/catch these
without risking circular imports.
"""


class SchemaError(ValueError):
    """Raised when a category field_schema is itself malformed."""

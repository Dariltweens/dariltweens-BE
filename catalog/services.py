"""Category-schema services — the core of the zero-migration extensibility model.

A Category stores a ``field_schema`` (JSONB) describing the custom fields its
Products may carry. A Product stores ``attributes`` (JSONB) holding the values.
These functions validate both the schema itself and attribute payloads against
it. They are pure (no Django, no DB) so they are cheap to unit-test and reusable
from serializers, services, and management commands alike.

Schema shape::

    {
        "version": 1,
        "fields": [
            {"name": "freshness", "type": "string", "required": true,
             "choices": ["fresh", "frozen"]},
            {"name": "weight", "type": "number", "min": 0, "max": 100},
        ],
    }
"""

from typing import Any

from catalog.exceptions import SchemaError

# Supported attribute types. Note bool is a subclass of int in Python, so the
# numeric checks below explicitly exclude bool to avoid True being "a number".
FIELD_TYPES = ("string", "number", "integer", "boolean")


def validate_field_schema(schema: Any) -> None:
    """Validate the *shape* of a category field_schema. Raises SchemaError.

    This guards the schema definition at write time so a malformed schema can
    never be persisted (and therefore never silently reject every product).
    """
    if not isinstance(schema, dict):
        raise SchemaError("field_schema must be an object.")
    fields = schema.get("fields")
    if not isinstance(fields, list):
        raise SchemaError("field_schema must contain a 'fields' list.")

    seen: set[str] = set()
    for field in fields:
        if not isinstance(field, dict):
            raise SchemaError("Each field must be an object.")
        name = field.get("name")
        if not isinstance(name, str) or not name:
            raise SchemaError("Each field requires a non-empty 'name'.")
        if name in seen:
            raise SchemaError(f"Duplicate field name: {name!r}.")
        seen.add(name)
        ftype = field.get("type")
        if ftype not in FIELD_TYPES:
            raise SchemaError(
                f"Field {name!r} has unknown type {ftype!r}; "
                f"expected one of {FIELD_TYPES}."
            )


def _type_matches(ftype: str, value: Any) -> bool:
    if ftype == "string":
        return isinstance(value, str)
    if ftype == "boolean":
        return isinstance(value, bool)
    if ftype == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if ftype == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return False


def _validate_value(field: dict, value: Any) -> list[str]:
    """Return a list of error strings for a single attribute value."""
    errors: list[str] = []
    ftype = field["type"]

    if not _type_matches(ftype, value):
        errors.append(f"Expected {ftype}, got {type(value).__name__}.")
        return errors  # further checks are meaningless on a type mismatch

    choices = field.get("choices")
    if choices is not None and value not in choices:
        errors.append(f"Must be one of {choices}.")

    if ftype in ("number", "integer"):
        minimum = field.get("min")
        maximum = field.get("max")
        if minimum is not None and value < minimum:
            errors.append(f"Must be >= {minimum}.")
        if maximum is not None and value > maximum:
            errors.append(f"Must be <= {maximum}.")

    return errors


def validate_attributes(schema: dict, attributes: Any) -> dict[str, list[str]]:
    """Validate a Product ``attributes`` payload against a category schema.

    Returns a mapping of ``field name -> [errors]``; an empty dict means valid.
    Errors are collected across all fields rather than failing on the first, so
    the API can report every problem at once. Unknown attributes are rejected to
    prevent silent attribute sprawl.
    """
    if not isinstance(attributes, dict):
        return {"attributes": ["Must be an object."]}

    fields = {f["name"]: f for f in schema.get("fields", [])}
    errors: dict[str, list[str]] = {}

    # Required + per-value checks for declared fields.
    for name, field in fields.items():
        if name not in attributes:
            if field.get("required", False):
                errors[name] = ["This field is required."]
            continue
        value_errors = _validate_value(field, attributes[name])
        if value_errors:
            errors[name] = value_errors

    # Reject anything not declared in the schema.
    for name in attributes:
        if name not in fields:
            errors.setdefault(name, []).append("Unknown field for this category.")

    return errors

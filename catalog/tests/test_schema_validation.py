"""Unit tests for the category-schema attribute validator.

This is the heart of the extensibility design: a Product's ``attributes`` JSONB
is validated against its Category's ``field_schema`` JSONB. The validator is a
pure function so it needs no database — hence @pytest.mark.unit.
"""

import pytest

from catalog.exceptions import SchemaError
from catalog.services import validate_attributes, validate_field_schema

pytestmark = pytest.mark.unit


FISH_SCHEMA = {
    "version": 1,
    "fields": [
        {"name": "freshness", "type": "string", "required": True,
         "choices": ["fresh", "frozen"]},
        {"name": "size_range", "type": "string", "required": False},
        {"name": "weight", "type": "number", "required": False, "min": 0, "max": 100},
        {"name": "wild_caught", "type": "boolean", "required": False},
    ],
}


# --- validate_attributes: happy paths --------------------------------------

def test_valid_attributes_pass():
    errors = validate_attributes(FISH_SCHEMA, {
        "freshness": "fresh",
        "size_range": "M",
        "weight": 12.5,
        "wild_caught": True,
    })
    assert errors == {}


def test_optional_fields_may_be_omitted():
    errors = validate_attributes(FISH_SCHEMA, {"freshness": "frozen"})
    assert errors == {}


# --- validate_attributes: failures -----------------------------------------

def test_missing_required_field_reports_error():
    errors = validate_attributes(FISH_SCHEMA, {"size_range": "L"})
    assert "freshness" in errors


def test_unknown_field_is_rejected():
    # Enforcing the schema strictly is what stops attribute sprawl.
    errors = validate_attributes(FISH_SCHEMA, {"freshness": "fresh", "color": "red"})
    assert "color" in errors


def test_wrong_type_reports_error():
    errors = validate_attributes(FISH_SCHEMA, {"freshness": "fresh", "weight": "heavy"})
    assert "weight" in errors


def test_value_not_in_choices_reports_error():
    errors = validate_attributes(FISH_SCHEMA, {"freshness": "lukewarm"})
    assert "freshness" in errors


def test_number_below_min_reports_error():
    errors = validate_attributes(FISH_SCHEMA, {"freshness": "fresh", "weight": -3})
    assert "weight" in errors


def test_number_above_max_reports_error():
    errors = validate_attributes(FISH_SCHEMA, {"freshness": "fresh", "weight": 999})
    assert "weight" in errors


def test_boolean_type_is_enforced():
    errors = validate_attributes(FISH_SCHEMA, {"freshness": "fresh", "wild_caught": "yes"})
    assert "wild_caught" in errors


def test_multiple_errors_collected_together():
    errors = validate_attributes(FISH_SCHEMA, {"weight": "heavy", "color": "red"})
    assert {"freshness", "weight", "color"} <= set(errors)


# --- validate_field_schema: schema definition is itself validated ----------

def test_wellformed_schema_passes():
    validate_field_schema(FISH_SCHEMA)  # should not raise


def test_schema_missing_fields_key_is_rejected():
    with pytest.raises(SchemaError):
        validate_field_schema({"version": 1})


def test_schema_field_without_name_is_rejected():
    with pytest.raises(SchemaError):
        validate_field_schema({"version": 1, "fields": [{"type": "string"}]})


def test_schema_with_unknown_type_is_rejected():
    with pytest.raises(SchemaError):
        validate_field_schema(
            {"version": 1, "fields": [{"name": "x", "type": "spaceship"}]}
        )


def test_schema_with_duplicate_field_names_is_rejected():
    with pytest.raises(SchemaError):
        validate_field_schema({"version": 1, "fields": [
            {"name": "x", "type": "string"},
            {"name": "x", "type": "number"},
        ]})

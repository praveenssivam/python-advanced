"""
06_exception_testing.py
=======================
Testing that code raises the right exceptions with the right messages.

Topics:
  1. pytest.raises as a context manager — assert type only
  2. match=r"..." — assert message matches a regex
  3. exc_info.value — inspect custom exception attributes
  4. Parametrized exception tests: N bad inputs × expected message patterns

Run:
    python demo/module-08/06_exception_testing.py
    pytest demo/module-08/06_exception_testing.py -v
"""

import sys
from typing import Optional

import pytest


# ══════════════════════════════════════════════════════════════════════════════
# PRODUCTION CODE
# ══════════════════════════════════════════════════════════════════════════════

class ValidationError(ValueError):
    """Raised when a record fails schema validation."""

    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message)
        self.field = field          # custom attribute: which field caused the error


def compute_score(value) -> float:
    """Returns a validated float score in [0, 100]."""
    if value is None:
        raise ValueError("score cannot be None")
    if not isinstance(value, (int, float)):
        raise ValueError("score must be numeric")
    if value < 0:
        raise ValueError(f"score must be positive (got {value})")
    if value > 100:
        raise ValueError(f"score must be <= 100 (got {value})")
    return float(value)


ALLOWED_TYPES = {"string", "integer", "float", "boolean", "date"}


def validate_schema(schema: dict) -> None:
    """
    Validates a schema definition dict.
    Raises ValidationError with a 'field' attribute identifying the bad key.
    """
    if "type" not in schema:
        raise ValidationError("schema must include a 'type' field", field="type")
    if schema["type"] not in ALLOWED_TYPES:
        raise ValidationError(
            f"unknown type '{schema['type']}'; allowed: {sorted(ALLOWED_TYPES)}",
            field="type",
        )
    max_len = schema.get("max_length")
    if max_len is not None and (not isinstance(max_len, int) or max_len <= 0):
        raise ValidationError(
            f"max_length must be a positive integer (got {max_len!r})",
            field="max_length",
        )


# ══════════════════════════════════════════════════════════════════════════════
# PART 1 — basic pytest.raises
#
# Pattern 1: assert only that the exception TYPE is raised
# Pattern 2: assert type + message contains a specific pattern (match=)
# Pattern 3: access the exception object via exc_info.value
# ══════════════════════════════════════════════════════════════════════════════

def test_raises_on_none_input():
    """Pattern 1: type only — passes for any ValueError."""
    with pytest.raises(ValueError):
        compute_score(None)


def test_raises_value_error_not_type_error():
    """
    Verify the EXCEPTION TYPE — don't rely on accident.
    If compute_score raised TypeError on string input, this test catches it.
    """
    with pytest.raises(ValueError):      # not TypeError
        compute_score("not-a-number")


def test_negative_score_message():
    """Pattern 2: match= is a regex tested against str(exc)."""
    with pytest.raises(ValueError, match=r"must be positive"):
        compute_score(-1)


def test_score_too_high_message():
    with pytest.raises(ValueError, match=r"<= 100"):
        compute_score(101)


def test_valid_score_does_not_raise():
    """Negative test: no exception for valid input."""
    result = compute_score(75.5)
    assert result == 75.5


def test_boundary_scores_do_not_raise():
    assert compute_score(0)   == 0.0
    assert compute_score(100) == 100.0


# ══════════════════════════════════════════════════════════════════════════════
# PART 2 — exc_info: inspect the exception object's attributes
# ══════════════════════════════════════════════════════════════════════════════

def test_inspect_validation_error_field_attribute():
    """
    Pattern 3: with pytest.raises(...) as exc_info:
    exc_info.value is the actual exception object — access any attribute.
    """
    with pytest.raises(ValidationError) as exc_info:
        validate_schema({"type": "uuid"})   # uuid is not in ALLOWED_TYPES

    exc = exc_info.value
    assert "unknown type" in str(exc)
    assert "uuid" in str(exc)
    assert exc.field == "type"              # our custom attribute


def test_schema_without_type_raises():
    with pytest.raises(ValidationError, match=r"must include a 'type'"):
        validate_schema({})


def test_negative_max_length_raises():
    with pytest.raises(ValidationError, match=r"max_length"):
        validate_schema({"type": "string", "max_length": -1})


def test_zero_max_length_raises():
    with pytest.raises(ValidationError) as exc_info:
        validate_schema({"type": "string", "max_length": 0})
    assert exc_info.value.field == "max_length"


# ══════════════════════════════════════════════════════════════════════════════
# PART 3 — parametrized exception tests
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("bad_input, match_pattern", [
    pytest.param(None,    r"cannot be None",    id="none_input"),
    pytest.param(-1,      r"must be positive",  id="negative_score"),
    pytest.param(101,     r"<= 100",            id="score_above_max"),
    pytest.param("text",  r"must be numeric",   id="string_input"),
    pytest.param([1, 2],  r"must be numeric",   id="list_input"),
])
def test_compute_score_error_messages(bad_input, match_pattern):
    """Every bad input must raise ValueError with the right message."""
    with pytest.raises(ValueError, match=match_pattern):
        compute_score(bad_input)


@pytest.mark.parametrize("bad_schema, expected_field", [
    pytest.param({"type": "unknown_type"},                "type",       id="unknown_type"),
    pytest.param({},                                      "type",       id="missing_type_key"),
    pytest.param({"type": "string", "max_length": 0},    "max_length", id="zero_max_length"),
    pytest.param({"type": "string", "max_length": "big"}, "max_length", id="string_max_length"),
])
def test_validate_schema_sets_correct_field_attribute(bad_schema, expected_field):
    """Assert both the exception type AND the field attribute on our custom exception."""
    with pytest.raises(ValidationError) as exc_info:
        validate_schema(bad_schema)
    assert exc_info.value.field == expected_field


# ══════════════════════════════════════════════════════════════════════════════
# DEMO: patterns reference
# ══════════════════════════════════════════════════════════════════════════════

def demo_raises_patterns() -> None:
    print("\n" + "═" * 78)
    print("  pytest.raises — THREE PATTERNS")
    print("═" * 78)
    print()
    print("  Pattern 1: check exception TYPE only")
    print("    with pytest.raises(ValueError):")
    print("        compute_score(None)")
    print()
    print("  Pattern 2: check type + message (match= is a regex)")
    print("    with pytest.raises(ValueError, match=r'must be positive'):")
    print("        compute_score(-1)")
    print()
    print("  Pattern 3: inspect the full exception object")
    print("    with pytest.raises(ValidationError) as exc_info:")
    print("        validate_schema({'type': 'uuid'})")
    print("    assert exc_info.value.field == 'type'")
    print()
    print("  Anti-pattern: bare raises(ValueError) passes for ANY ValueError.")
    print("  Always add match= when the message content matters.")
    print()
    print("  Parametrized exception tests:")
    print("    @pytest.mark.parametrize('bad_input, pattern', [...])")
    print("    def test_errors(bad_input, pattern):")
    print("        with pytest.raises(ValueError, match=pattern):")
    print("            compute_score(bad_input)")
    print()


def main() -> None:
    demo_raises_patterns()

    print("═" * 78)
    print("  RUNNING EXCEPTION TESTS")
    print("═" * 78)
    print()
    ret = pytest.main([__file__, "-v", "--tb=short", "--no-header"])
    sys.exit(ret)


if __name__ == "__main__":
    main()

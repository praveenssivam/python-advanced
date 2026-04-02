"""Unit tests for all three validator functions."""

from validator import validate_category, validate_input, validate_schema


class TestValidateInput:
    """Tests for validate_input — checks presence of 'name' and 'value' keys."""

    def test_valid_payload(self) -> None:
        """Both required keys present — expect ok."""
        result = validate_input({"name": "test", "value": 1})
        assert result["status"] == "ok"

    def test_missing_name(self) -> None:
        """'name' is absent — expect error mentioning 'name'."""
        result = validate_input({"value": 1})
        assert result["status"] == "error"
        assert "name" in result["message"]

    def test_missing_value(self) -> None:
        """'value' is absent — expect error mentioning 'value'."""
        result = validate_input({"name": "test"})
        assert result["status"] == "error"
        assert "value" in result["message"]

    def test_empty_payload(self) -> None:
        """Empty dict — expect error (first missing key reported)."""
        result = validate_input({})
        assert result["status"] == "error"

    def test_extra_keys_are_allowed(self) -> None:
        """Extra keys beyond the required two must not cause an error."""
        result = validate_input({"name": "test", "value": 1, "category": "premium"})
        assert result["status"] == "ok"


class TestValidateSchema:
    """Tests for validate_schema — checks 'value' type and range."""

    def test_valid_positive_integer(self) -> None:
        """Positive integer value — expect ok."""
        result = validate_schema({"value": 10})
        assert result["status"] == "ok"

    def test_value_is_string(self) -> None:
        """String value — expect error mentioning 'integer'."""
        result = validate_schema({"value": "ten"})
        assert result["status"] == "error"
        assert "integer" in result["message"]

    def test_value_is_zero(self) -> None:
        """Zero is not positive — expect error mentioning 'positive'."""
        result = validate_schema({"value": 0})
        assert result["status"] == "error"
        assert "positive" in result["message"]

    def test_value_is_negative(self) -> None:
        """Negative integer — expect error mentioning 'positive'."""
        result = validate_schema({"value": -5})
        assert result["status"] == "error"
        assert "positive" in result["message"]

    def test_value_is_float(self) -> None:
        """Float value — expect error (floats are not int)."""
        result = validate_schema({"value": 3.14})
        assert result["status"] == "error"

    def test_missing_value_key(self) -> None:
        """Payload has no 'value' key at all — expect error."""
        result = validate_schema({})
        assert result["status"] == "error"


class TestValidateCategory:
    """Tests for validate_category — 'category' is an optional field."""

    def test_valid_category(self) -> None:
        """Non-empty string category — expect ok."""
        result = validate_category({"category": "premium"})
        assert result["status"] == "ok"

    def test_category_absent_is_valid(self) -> None:
        """'category' is optional — its absence must not produce an error.

        This test documents the intentional design decision: validate_category
        should return ok immediately when the key is not present in the payload.
        """
        result = validate_category({})
        assert result["status"] == "ok"

    def test_empty_string_category(self) -> None:
        """Empty string is an invalid category — expect error mentioning 'non-empty'."""
        result = validate_category({"category": ""})
        assert result["status"] == "error"
        assert "non-empty" in result["message"]

    def test_whitespace_only_category(self) -> None:
        """Whitespace-only string must be treated as empty — expect error."""
        result = validate_category({"category": "   "})
        assert result["status"] == "error"

    def test_non_string_category(self) -> None:
        """Non-string category (e.g. integer) — expect error."""
        result = validate_category({"category": 123})
        assert result["status"] == "error"

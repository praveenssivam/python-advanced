"""
tests/test_rules.py — Unit tests for built-in validation rules.

─────────────────────────────────────────────────────────
DAY 5 TASK
─────────────────────────────────────────────────────────
Write exactly 5 tests (the ones named below). Then run:

    pytest --cov=src/validify --cov-fail-under=70

All 5 tests must pass. The coverage threshold must be met.

Use the fixtures from conftest.py: valid_record, null_record, out_of_range_record.
"""

import pytest

# Uncomment these imports once you have implemented the relevant modules:
# from validify.rules.built_in import NullCheckRule, RangeRule
# from validify.rules.registry import ValidatorRegistry


# ---------------------------------------------------------------------------
# Test 1
# ---------------------------------------------------------------------------
def test_null_check_passes_when_field_present(valid_record):
    """NullCheckRule.validate() should return True for a non-empty vendor_id."""
    # rule = NullCheckRule(field="vendor_id")
    # assert rule.validate(valid_record) is True
    pytest.skip("implement me")


# ---------------------------------------------------------------------------
# Test 2
# ---------------------------------------------------------------------------
def test_null_check_fails_when_field_empty(null_record):
    """NullCheckRule.validate() should return False when passenger_count is ''."""
    # rule = NullCheckRule(field="passenger_count")
    # assert rule.validate(null_record) is False
    pytest.skip("implement me")


# ---------------------------------------------------------------------------
# Test 3
# ---------------------------------------------------------------------------
def test_range_rule_passes_within_bounds(valid_record):
    """RangeRule should pass when passenger_count == 1 and bounds are [1, 8]."""
    # rule = RangeRule(field="passenger_count", min_val=1, max_val=8)
    # assert rule.validate(valid_record) is True
    pytest.skip("implement me")


# ---------------------------------------------------------------------------
# Test 4
# ---------------------------------------------------------------------------
def test_range_rule_fails_above_max(out_of_range_record):
    """RangeRule should fail when passenger_count == 12 and max is 8."""
    # rule = RangeRule(field="passenger_count", min_val=1, max_val=8)
    # assert rule.validate(out_of_range_record) is False
    pytest.skip("implement me")


# ---------------------------------------------------------------------------
# Test 5
# ---------------------------------------------------------------------------
def test_registry_has_null_check_rule():
    """
    Importing NullCheckRule should auto-register it in ValidatorRegistry.
    ValidatorRegistry.get("null_check_rule") should return the NullCheckRule class.
    """
    # from validify.rules.built_in import NullCheckRule
    # assert ValidatorRegistry.get("null_check_rule") is NullCheckRule
    pytest.skip("implement me")


# ---------------------------------------------------------------------------
# Stretch tests (optional — write after the 5 mandatory ones)
# ---------------------------------------------------------------------------
# def test_range_rule_fails_below_min ...
# def test_null_check_fails_when_field_missing ...
# def test_rule_factory_loads_from_yaml ...

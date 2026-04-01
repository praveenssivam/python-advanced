"""
02_pytest_basics.py
===================
pytest — cleaner syntax and much better failure messages than unittest.

Topics:
  1. Plain test functions vs TestCase classes
  2. pytest -v output format and test naming
  3. Why `assert a == b` beats `self.assertEqual(a, b)`
  4. Running pytest from code with pytest.main()

Run:
    python demo/module-08/02_pytest_basics.py
    pytest demo/module-08/02_pytest_basics.py -v
"""

import sys
import re
from dataclasses import dataclass
from datetime import date
from typing import Optional

import pytest
import unittest


# ══════════════════════════════════════════════════════════════════════════════
# PRODUCTION CODE
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class ValidationResult:
    is_valid: bool
    error: Optional[str] = None


_DATE_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$")


def validate_date(date_str: str) -> ValidationResult:
    """Validates an ISO 8601 date string (YYYY-MM-DD), including leap-year logic."""
    if not date_str:
        return ValidationResult(False, "date cannot be empty")
    if not _DATE_RE.match(date_str):
        return ValidationResult(False, "date must be YYYY-MM-DD with valid ranges")
    try:
        year, month, day = map(int, date_str.split("-"))
        date(year, month, day)   # raises ValueError for e.g. Feb 30
        return ValidationResult(True)
    except ValueError:
        return ValidationResult(False, "invalid calendar date")


# ══════════════════════════════════════════════════════════════════════════════
# APPROACH A — unittest.TestCase (old style)
#
# Note:
#   - Every assertion uses a method name  (self.assertTrue, self.assertEqual)
#   - Must inherit TestCase to be discovered
#   - Failure message: "False is not true" — tells you nothing
# ══════════════════════════════════════════════════════════════════════════════

class TestValidateDateUnittest(unittest.TestCase):
    """unittest.TestCase style — kept here for direct comparison."""

    def test_valid_date(self):
        result = validate_date("2024-01-15")
        self.assertTrue(result.is_valid)

    def test_empty_string_fails(self):
        result = validate_date("")
        self.assertFalse(result.is_valid)
        self.assertIn("empty", result.error)

    def test_invalid_month_13_fails(self):
        result = validate_date("2024-13-01")
        self.assertFalse(result.is_valid)


# ══════════════════════════════════════════════════════════════════════════════
# APPROACH B — plain pytest functions (preferred for new code)
#
# Note:
#   - Any function named test_* is discovered automatically
#   - No class inheritance required
#   - plain `assert` — pytest rewrites it to show actual/expected values
#   - On failure: "assert False  where False = ValidationResult(...).is_valid"
# ══════════════════════════════════════════════════════════════════════════════

def test_valid_date_passes():
    result = validate_date("2024-06-15")
    assert result.is_valid                  # plain assert — pytest enhances on failure


def test_valid_leap_day_passes():
    result = validate_date("2024-02-29")    # 2024 is a leap year
    assert result.is_valid


def test_empty_date_fails():
    result = validate_date("")
    assert not result.is_valid
    assert "empty" in result.error


def test_invalid_month_13_fails():
    result = validate_date("2024-13-01")
    assert not result.is_valid


def test_non_leap_year_feb29_fails():
    result = validate_date("2023-02-29")    # 2023 is NOT a leap year
    assert not result.is_valid


def test_non_zero_padded_fails():
    result = validate_date("2024-1-5")      # must be 01 and 05
    assert not result.is_valid


def test_impossible_date_feb30_fails():
    result = validate_date("2024-02-30")
    assert not result.is_valid


def test_result_is_valid_true_for_boundary_dates():
    assert validate_date("2024-01-01").is_valid   # first day of year
    assert validate_date("2024-12-31").is_valid   # last day of year
    assert validate_date("2024-03-31").is_valid   # 31-day month


# ══════════════════════════════════════════════════════════════════════════════
# DEMO: side-by-side comparison
# ══════════════════════════════════════════════════════════════════════════════

def demo_comparison_table() -> None:
    print("\n" + "═" * 78)
    print("  unittest.TestCase  vs  plain pytest  — COMPARISON")
    print("═" * 78)
    print()
    rows = [
        ("Assertion style",  "self.assertEqual(a, b)",    "assert a == b"),
        ("Failure message",  '"False is not true"',       "shows actual/expected values"),
        ("Fixtures",         "setUp/tearDown per class",  "composable @pytest.fixture"),
        ("Parametrize",      "manual loop or subTest",    "@pytest.mark.parametrize"),
        ("Discovery",        "must inherit TestCase",     "any def test_*()"),
        ("Plugins",          "limited",                   "1000+ (cov, asyncio, mock…)"),
    ]
    print(f"  {'Feature':<24}  {'unittest':<30}  pytest")
    print(f"  {'-'*24}  {'-'*30}  {'-'*30}")
    for feature, ut, pt in rows:
        print(f"  {feature:<24}  {ut:<30}  {pt}")
    print()
    print("  Rule: prefer plain pytest functions for new code.")
    print("  Keep unittest.TestCase when maintaining older codebases.")
    print()

    print("  pytest FAILURE MESSAGE example:")
    print("    FAILED test_validators.py::test_valid_date_passes")
    print("    AssertionError: assert False")
    print("     +  where False = ValidationResult(is_valid=False, error='domain missing').is_valid")
    print()


def main() -> None:
    demo_comparison_table()

    print("═" * 78)
    print("  RUNNING TESTS WITH pytest.main()")
    print("═" * 78)
    print()
    ret = pytest.main([__file__, "-v", "--tb=short", "--no-header"])
    sys.exit(ret)


if __name__ == "__main__":
    main()

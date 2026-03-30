"""
04_parametrize.py
=================
pytest.mark.parametrize — test N cases with one function body.

Topics:
  1. @pytest.mark.parametrize with a list of tuples
  2. pytest.param(..., id="...") for readable test names
  3. Stacking two @parametrize decorators (cartesian product)
  4. How pytest names each case in the output

Run:
    python demo/module-08/04_parametrize.py
    pytest demo/module-08/04_parametrize.py -v
"""

import sys
import re
from dataclasses import dataclass
from datetime import date
from typing import Optional

import pytest


# ══════════════════════════════════════════════════════════════════════════════
# PRODUCTION CODE
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class ValidationResult:
    is_valid: bool
    error: Optional[str] = None


_DATE_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$")


def validate_date(date_str: str) -> ValidationResult:
    if not date_str:
        return ValidationResult(False, "date cannot be empty")
    if not _DATE_RE.match(date_str):
        return ValidationResult(False, "date must be YYYY-MM-DD format")
    try:
        year, month, day = map(int, date_str.split("-"))
        date(year, month, day)
        return ValidationResult(True)
    except ValueError:
        return ValidationResult(False, "invalid calendar date")


def normalize_status(status: str) -> str:
    """Maps raw status strings to canonical values."""
    mapping = {
        "active":   "active",  "enabled":  "active",  "on":    "active",
        "inactive": "inactive","disabled": "inactive", "off":   "inactive",
        "pending":  "pending", "waiting":  "pending",
    }
    return mapping.get(status.lower().strip(), "unknown")


# ══════════════════════════════════════════════════════════════════════════════
# PART 1 — basic parametrize: list of (input, expected) tuples
#
# pytest runs this as 8 separate test cases.
# Auto-generated names use the parameter VALUES — readable for simple types,
# but ugly for empty strings, None, etc. (see the "" case below).
#
# Output preview:
#   test_validate_date[2024-01-15-True]   PASSED
#   test_validate_date[-False1]           PASSED  ← empty string becomes "-False1"
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("date_str, expected_valid", [
    ("2024-01-15", True),
    ("2024-13-01", False),   # month 13 does not exist
    ("2024-00-01", False),   # month 0 does not exist
    ("not-a-date", False),
    ("",           False),   # ← auto-name will be "-False1" — add id= to fix
    ("2024-1-5",   False),   # not zero-padded
    ("2024-02-29", True),    # 2024 IS a leap year
    ("2023-02-29", False),   # 2023 is NOT a leap year
])
def test_validate_date(date_str, expected_valid):
    result = validate_date(date_str)
    assert result.is_valid == expected_valid


# ══════════════════════════════════════════════════════════════════════════════
# PART 2 — pytest.param with explicit IDs
#
# IDs appear in the test name:
#   test_validate_date_named[leap_year_valid]     PASSED
#   test_validate_date_named[non_leap_year_feb29] PASSED
#
# Rule: always add id= when the value is empty, None, or ambiguous.
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("date_str, expected_valid", [
    pytest.param("2024-06-01",  True,  id="normal_valid_date"),
    pytest.param("2024-02-29",  True,  id="leap_year_valid"),
    pytest.param("2023-02-29",  False, id="non_leap_year_feb29"),
    pytest.param("2024-02-30",  False, id="impossible_feb30"),
    pytest.param("2024-04-31",  False, id="april_has_only_30_days"),
    pytest.param("",            False, id="empty_string"),
    pytest.param("2024-12-31",  True,  id="last_day_of_year"),
    pytest.param("2024-01-32",  False, id="day_32_invalid"),
])
def test_validate_date_named(date_str, expected_valid):
    """Same logic as above — the only difference is readable test names."""
    result = validate_date(date_str)
    assert result.is_valid == expected_valid


# ══════════════════════════════════════════════════════════════════════════════
# PART 3 — parametrize status normalization
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("raw, expected", [
    pytest.param("active",    "active",   id="already_active"),
    pytest.param("ACTIVE",    "active",   id="uppercase_active"),
    pytest.param("enabled",   "active",   id="synonym_enabled"),
    pytest.param("on",        "active",   id="synonym_on"),
    pytest.param("disabled",  "inactive", id="synonym_disabled"),
    pytest.param("off",       "inactive", id="synonym_off"),
    pytest.param("pending",   "pending",  id="already_pending"),
    pytest.param("waiting",   "pending",  id="synonym_waiting"),
    pytest.param("unknown",   "unknown",  id="unrecognized_status"),
    pytest.param("  active ", "active",   id="whitespace_trimmed"),
])
def test_normalize_status(raw, expected):
    assert normalize_status(raw) == expected


# ══════════════════════════════════════════════════════════════════════════════
# PART 4 — stacking two @parametrize decorators (cartesian product)
#
# N×M test cases are generated: every combination of the two parameter lists.
# Here: 3 prefixes × 2 dates = 6 tests.
#
# Output:
#   test_whitespace_prefix[\t-2024-01-15]   PASSED
#   test_whitespace_prefix[-2024-12-31]     PASSED  (empty prefix passes)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("prefix", [
    pytest.param("",   id="no_prefix"),
    pytest.param(" ",  id="space_prefix"),
    pytest.param("\t", id="tab_prefix"),
])
@pytest.mark.parametrize("date_str", [
    pytest.param("2024-01-15", id="jan15"),
    pytest.param("2024-12-31", id="dec31"),
])
def test_whitespace_prefix_handling(prefix, date_str):
    """Dates with leading whitespace must be rejected; clean dates must pass."""
    result = validate_date(prefix + date_str)
    if prefix:
        assert not result.is_valid    # leading whitespace = invalid format
    else:
        assert result.is_valid


# ══════════════════════════════════════════════════════════════════════════════
# DEMO: naming output walkthrough
# ══════════════════════════════════════════════════════════════════════════════

def demo_naming_output() -> None:
    print("\n" + "═" * 78)
    print("  HOW pytest NAMES PARAMETRIZED TEST CASES")
    print("═" * 78)
    print()
    print("  WITHOUT id= (auto-generated from values):")
    print("    test_validate_date[2024-01-15-True]   PASSED")
    print("    test_validate_date[2024-13-01-False]  PASSED")
    print("    test_validate_date[-False1]            PASSED  ← empty string!")
    print()
    print("  WITH pytest.param(..., id=...) :")
    print("    test_validate_date_named[leap_year_valid]      PASSED")
    print("    test_validate_date_named[non_leap_year_feb29]  PASSED")
    print("    test_validate_date_named[empty_string]         PASSED")
    print()
    print("  STACKED decorators (N×M cartesian product):")
    print("    test_whitespace_prefix[jan15-no_prefix]    PASSED")
    print("    test_whitespace_prefix[jan15-space_prefix] PASSED")
    print("    test_whitespace_prefix[jan15-tab_prefix]   PASSED")
    print("    test_whitespace_prefix[dec31-no_prefix]    PASSED")
    print("    ...  (2 dates × 3 prefixes = 6 total)")
    print()
    print("  One failure shows EXACTLY which input failed — no loop noise.")
    print()


def main() -> None:
    demo_naming_output()

    print("═" * 78)
    print("  RUNNING PARAMETRIZED TESTS")
    print("═" * 78)
    print()
    ret = pytest.main([__file__, "-v", "--tb=short", "--no-header"])
    sys.exit(ret)


if __name__ == "__main__":
    main()

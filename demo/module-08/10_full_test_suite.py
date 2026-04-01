"""
10_full_test_suite.py
=====================
Complete test suite for a validation service — all patterns in one file.

Topics:
  1. Happy path tests
  2. Edge cases and boundary values
  3. Exception path tests (pytest.raises)
  4. Batch / partial-failure behavior
  5. Async validation tests (pytest-asyncio)
  6. Property-based invariant tests (Hypothesis)

This file demonstrates how the patterns from demos 01–09 compose into a
real, production-grade test suite.

Run:
    python demo/module-08/10_full_test_suite.py
    pytest demo/module-08/10_full_test_suite.py -v --asyncio-mode=auto
"""

import sys
import asyncio
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st


# ══════════════════════════════════════════════════════════════════════════════
# PRODUCTION SERVICE
# ══════════════════════════════════════════════════════════════════════════════

class ValidationError(ValueError):
    """Raised on invalid field values; carries the offending field name."""

    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message)
        self.field = field


@dataclass
class RecordResult:
    record_id: int
    is_valid:  bool
    error:     Optional[str] = None


# ── validators ────────────────────────────────────────────────────────────────

_EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
_DATE_RE  = re.compile(r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$")


def validate_email(email: str) -> None:
    """Raises ValidationError if the email is invalid."""
    if not email:
        raise ValidationError("email cannot be empty", field="email")
    if len(email) > 254:
        raise ValidationError("email too long", field="email")
    if not _EMAIL_RE.fullmatch(email):
        raise ValidationError(f"invalid email: {email}", field="email")


def validate_date(date_str: str) -> None:
    """Raises ValidationError if the ISO 8601 date is invalid."""
    if not date_str:
        raise ValidationError("date cannot be empty", field="date")
    if not _DATE_RE.match(date_str):
        raise ValidationError(f"invalid date format: {date_str}", field="date")
    try:
        y, m, d = map(int, date_str.split("-"))
        date(y, m, d)
    except ValueError:
        raise ValidationError(f"invalid calendar date: {date_str}", field="date")


def normalize_name(name: str) -> str:
    """Remove control chars, collapse whitespace, apply title case."""
    cleaned = "".join(
        ch for ch in name
        if unicodedata.category(ch)[0] != "C"
    )
    return " ".join(cleaned.split()).title()


def validate_record(record: dict) -> RecordResult:
    """Validate a single record; returns a RecordResult (never raises)."""
    rid = record.get("id", -1)
    try:
        if not isinstance(record.get("id"), int) or record["id"] <= 0:
            raise ValidationError("id must be a positive integer", field="id")
        name = record.get("name", "")
        if not name or not str(name).strip():
            raise ValidationError("name cannot be empty", field="name")
        if "email" in record:
            validate_email(record["email"])
        if "signup_date" in record:
            validate_date(record["signup_date"])
    except ValidationError as exc:
        return RecordResult(record_id=rid, is_valid=False, error=str(exc))
    return RecordResult(record_id=rid, is_valid=True)


def validate_batch(records: list[dict]) -> list[RecordResult]:
    """
    Validate all records.  Failures are captured per-record — we never raise.
    The caller receives a full result list and decides how to handle failures
    (log, quarantine, re-queue, etc.).
    """
    return [validate_record(r) for r in records]


class AsyncValidationService:
    """Async wrapper for use in coroutine-based pipeline stages."""

    async def validate(self, record: dict) -> RecordResult:
        await asyncio.sleep(0)          # yield to event loop
        return validate_record(record)

    async def validate_batch(self, records: list[dict]) -> list[RecordResult]:
        return [await self.validate(r) for r in records]


# ══════════════════════════════════════════════════════════════════════════════
# FIXTURES
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def valid_record() -> dict:
    return {
        "id":          1,
        "name":        "Alice Smith",
        "email":       "alice@example.com",
        "signup_date": "2024-03-15",
    }


@pytest.fixture
def service() -> AsyncValidationService:
    return AsyncValidationService()


# ══════════════════════════════════════════════════════════════════════════════
# 1 — HAPPY PATH TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestHappyPath:

    def test_minimal_valid_record(self):
        result = validate_record({"id": 1, "name": "Alice"})
        assert result.is_valid
        assert result.error is None

    def test_full_valid_record(self, valid_record):
        result = validate_record(valid_record)
        assert result.is_valid

    def test_result_carries_correct_record_id(self, valid_record):
        result = validate_record(valid_record)
        assert result.record_id == valid_record["id"]

    def test_record_without_optional_fields_passes(self):
        """email and signup_date are optional."""
        result = validate_record({"id": 42, "name": "Bob"})
        assert result.is_valid


# ══════════════════════════════════════════════════════════════════════════════
# 2 — EDGE CASES AND BOUNDARY VALUES
# ══════════════════════════════════════════════════════════════════════════════

class TestEdgeCases:

    @pytest.mark.parametrize("record", [
        pytest.param({"id": 1,          "name": "X"},           id="min_name"),
        pytest.param({"id": 999_999,    "name": "Alice"},        id="large_id"),
        pytest.param({"id": 1,          "name": "A" * 200},      id="long_name"),
        pytest.param({"id": 1,          "name": "Alice",
                       "email": "a@b.co"},                       id="short_tld"),
        pytest.param({"id": 1,          "name": "Alice",
                       "signup_date": "2024-02-29"},              id="leap_day_2024"),
    ])
    def test_valid_edge_cases(self, record):
        assert validate_record(record).is_valid

    @pytest.mark.parametrize("bad_record, expected_field", [
        pytest.param({"id": 0,  "name": "Alice"},                "id",    id="id_zero"),
        pytest.param({"id": -1, "name": "Alice"},                "id",    id="id_negative"),
        pytest.param({"id": 1,  "name": ""},                     "name",  id="empty_name"),
        pytest.param({"id": 1,  "name": "   "},                  "name",  id="whitespace_name"),
        pytest.param({"id": 1,  "name": "Alice",
                       "email": "notanemail"},                    "email", id="bad_email"),
        pytest.param({"id": 1,  "name": "Alice",
                       "signup_date": "2024-13-01"},              "date",  id="bad_month"),
        pytest.param({"id": 1,  "name": "Alice",
                       "signup_date": "2023-02-29"},              "date",  id="non_leap_feb29"),
    ])
    def test_invalid_edge_cases(self, bad_record, expected_field):
        result = validate_record(bad_record)
        assert not result.is_valid
        assert expected_field in result.error


# ══════════════════════════════════════════════════════════════════════════════
# 3 — EXCEPTION PATH TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestExceptionPaths:

    def test_invalid_email_raises(self):
        with pytest.raises(ValidationError, match=r"invalid email"):
            validate_email("notanemail")

    def test_empty_email_raises(self):
        with pytest.raises(ValidationError, match=r"cannot be empty"):
            validate_email("")

    def test_too_long_email_raises(self):
        with pytest.raises(ValidationError, match=r"too long"):
            validate_email("a" * 250 + "@b.com")

    def test_invalid_date_format_raises(self):
        with pytest.raises(ValidationError, match=r"invalid date format"):
            validate_date("01-15-2024")         # wrong order

    def test_non_calendar_date_raises(self):
        with pytest.raises(ValidationError):
            validate_date("2023-02-29")         # 2023 is not a leap year

    def test_validation_error_carries_field(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_email("bad")
        assert exc_info.value.field == "email"


# ══════════════════════════════════════════════════════════════════════════════
# 4 — BATCH / PARTIAL FAILURE
# ══════════════════════════════════════════════════════════════════════════════

class TestBatchBehavior:

    def test_all_valid_batch(self, valid_record):
        batch = [valid_record, {**valid_record, "id": 2, "name": "Bob"}]
        results = validate_batch(batch)
        assert all(r.is_valid for r in results)
        assert len(results) == 2

    def test_partial_failure_does_not_stop_batch(self):
        batch = [
            {"id": 1, "name": "Alice"},
            {"id": 0, "name": ""},          # invalid — two bad fields
            {"id": 3, "name": "Carol"},
        ]
        results = validate_batch(batch)
        assert len(results) == 3            # all processed, none skipped
        assert results[0].is_valid
        assert not results[1].is_valid
        assert results[2].is_valid

    def test_empty_batch_returns_empty_list(self):
        assert validate_batch([]) == []

    def test_all_invalid_batch(self):
        batch = [{"id": 0, "name": ""}, {"id": -1, "name": None}]
        results = validate_batch(batch)
        assert not any(r.is_valid for r in results)

    def test_each_failure_has_a_non_empty_error(self):
        batch = [{"id": 0, "name": ""}, {"id": 1, "name": "", "email": "bad"}]
        results = validate_batch(batch)
        for r in results:
            assert not r.is_valid
            assert r.error and len(r.error) > 0


# ══════════════════════════════════════════════════════════════════════════════
# 5 — ASYNC TESTS
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_async_validate_valid_record(service, valid_record):
    result = await service.validate(valid_record)
    assert result.is_valid


@pytest.mark.asyncio
async def test_async_validate_invalid_record(service):
    result = await service.validate({"id": 0, "name": ""})
    assert not result.is_valid


@pytest.mark.asyncio
async def test_async_validate_batch_mixed(service, valid_record):
    batch = [valid_record, {"id": 0, "name": ""}]
    results = await service.validate_batch(batch)
    assert results[0].is_valid
    assert not results[1].is_valid


@pytest.mark.asyncio
async def test_async_batch_returns_result_for_every_record(service, valid_record):
    batch = [valid_record] * 5
    results = await service.validate_batch(batch)
    assert len(results) == 5
    assert all(r.is_valid for r in results)


# ══════════════════════════════════════════════════════════════════════════════
# 6 — PROPERTY-BASED TESTS
# ══════════════════════════════════════════════════════════════════════════════

@given(st.fixed_dictionaries({
    "id":   st.integers(min_value=1, max_value=10_000),
    "name": st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Zs")),
        min_size=1,
        max_size=100,
    ),
}))
@settings(max_examples=100)
def test_property_valid_records_always_pass(record):
    """Any record with a positive int id and a non-blank name must be valid."""
    assume(record["name"].strip())      # skip whitespace-only names
    result = validate_record(record)
    assert result.is_valid, f"Unexpected failure: {result.error} for {record}"


@given(st.text(min_size=0, max_size=200))
@settings(max_examples=150)
def test_property_normalize_name_is_idempotent(name):
    """normalize_name applied twice equals applied once — for all inputs."""
    once  = normalize_name(name)
    twice = normalize_name(once)
    assert once == twice


@given(st.text(min_size=0, max_size=200))
@settings(max_examples=100)
def test_property_validate_record_never_raises(name):
    """validate_record must never raise — errors go into RecordResult.error."""
    record = {"id": 1, "name": name}
    try:
        result = validate_record(record)
        assert isinstance(result, RecordResult)
    except Exception as exc:
        pytest.fail(f"validate_record raised unexpectedly: {exc!r}")


# ══════════════════════════════════════════════════════════════════════════════
# DEMO: test pyramid summary
# ══════════════════════════════════════════════════════════════════════════════

def demo_suite_summary() -> None:
    print("\n" + "═" * 78)
    print("  FULL TEST SUITE — COVERAGE SUMMARY")
    print("═" * 78)
    print()
    groups = [
        ("Happy Path",      "TestHappyPath",       "unit",     4),
        ("Edge Cases",      "TestEdgeCases",       "unit",    12),
        ("Exception Paths", "TestExceptionPaths",  "unit",     6),
        ("Batch Behavior",  "TestBatchBehavior",   "unit",     5),
        ("Async Behavior",  "test_async_*",        "unit",     4),
        ("Property-Based",  "test_property_*",     "property", 3),
    ]
    total = 0
    print(f"  {'Category':<20}  {'Pattern':<30}  {'Type':<10}  Tests")
    print(f"  {'-'*20}  {'-'*30}  {'-'*10}  -----")
    for cat, pattern, tp, count in groups:
        print(f"  {cat:<20}  {pattern:<30}  {tp:<10}  {count}")
        total += count
    print(f"  {'─'*68}")
    print(f"  {'TOTAL':<20}  {'':30}  {'':10}  {total}")
    print()
    print("  Pyramid balance (this suite): unit (31) >> property (3) >> integration (0)")
    print("  Integration tests (real DB, real HTTP) live in a separate tests/ directory,")
    print("  run on CI only — not as part of the local fast feedback loop.")
    print()


def main() -> None:
    demo_suite_summary()

    print("═" * 78)
    print("  RUNNING FULL TEST SUITE  (--asyncio-mode=auto for async tests)")
    print("═" * 78)
    print()
    ret = pytest.main([
        __file__, "-v", "--tb=short", "--no-header",
        "--asyncio-mode=auto",
    ])
    sys.exit(ret)


if __name__ == "__main__":
    main()

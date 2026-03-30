"""
03_fixtures.py
==============
pytest fixtures — shared setup, teardown, and dependency injection.

Topics:
  1. @pytest.fixture — setup with yield, teardown after yield
  2. Fixture injection: one fixture depending on another
  3. Fixture scopes: function (default) vs module
  4. Function-scope isolation: each test gets a fresh object

Run:
    python demo/module-08/03_fixtures.py
    pytest demo/module-08/03_fixtures.py -v -s
"""

import sys
import time
from dataclasses import dataclass, field
from typing import Optional

import pytest


# ══════════════════════════════════════════════════════════════════════════════
# PRODUCTION CODE
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Schema:
    name: str
    required_fields: list[str]


@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[str] = field(default_factory=list)


class ValidationService:
    """Validates records against named schemas."""

    def __init__(self, schemas: dict[str, Schema]):
        self._schemas = schemas
        self.calls = 0        # visible call counter — used in isolation test

    def validate(self, record: dict, schema_name: str) -> ValidationResult:
        self.calls += 1
        schema = self._schemas.get(schema_name)
        if schema is None:
            return ValidationResult(False, [f"unknown schema: {schema_name}"])
        missing = [
            f"missing required field: {f}"
            for f in schema.required_fields
            if f not in record or record[f] is None
        ]
        return ValidationResult(len(missing) == 0, missing)


# ══════════════════════════════════════════════════════════════════════════════
# FIXTURES
#
# Placement rule:
#   - Fixtures used by one file  → define at top of that file
#   - Fixtures shared across files → put in tests/conftest.py
#     (pytest auto-discovers conftest.py; no import needed)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def sample_record() -> dict:
    """
    scope="function" (default): recreated fresh for every test that requests it.
    Return a plain dict — the caller gets a copy via dict spread if they mutate it.
    """
    return {"id": 1, "name": "Alice", "email": "alice@example.com", "score": 9.5}


@pytest.fixture
def schemas() -> dict[str, Schema]:
    """Registry of test schemas."""
    return {
        "user":    Schema("user",    ["id", "name", "email"]),
        "product": Schema("product", ["id", "name", "price"]),
    }


@pytest.fixture
def validation_service(schemas) -> ValidationService:
    """
    This fixture DEPENDS on the `schemas` fixture.
    pytest resolves the dependency by name and injects it automatically.

    yield separates setup (before) from teardown (after the test).
    teardown runs even if the test fails — analogous to try/finally.
    """
    # ── setup ─────────────────────────────────────────────────────────────────
    svc = ValidationService(schemas)
    yield svc
    # ── teardown (after the test) ─────────────────────────────────────────────
    # If svc held a real DB connection: svc.close()
    # Nothing to release here — shown for pattern illustration.


@pytest.fixture(scope="module")
def expensive_resource():
    """
    scope="module": created ONCE for the entire module, shared by all tests.
    Use for slow resources: DB containers, server processes, large data loads.
    The -s flag (no capture) shows the print statements so you can see when
    setup/teardown actually run.
    """
    print("\n  [fixture] expensive_resource — SETUP (once per module)")
    resource = {"connection": "mock-db-conn", "created_at": time.monotonic()}
    yield resource
    print("\n  [fixture] expensive_resource — TEARDOWN (once per module)")


# ══════════════════════════════════════════════════════════════════════════════
# TESTS
# ══════════════════════════════════════════════════════════════════════════════

def test_valid_user_record(validation_service, sample_record):
    result = validation_service.validate(sample_record, "user")
    assert result.is_valid
    assert result.errors == []


def test_missing_email_field_fails(validation_service, sample_record):
    record = {k: v for k, v in sample_record.items() if k != "email"}
    result = validation_service.validate(record, "user")
    assert not result.is_valid
    assert any("email" in e for e in result.errors)


def test_unknown_schema_name_fails(validation_service, sample_record):
    result = validation_service.validate(sample_record, "nonexistent_schema")
    assert not result.is_valid
    assert any("unknown schema" in e for e in result.errors)


def test_product_schema_validates_correctly(validation_service):
    product = {"id": 100, "name": "Widget", "price": 9.99}
    result = validation_service.validate(product, "product")
    assert result.is_valid


def test_function_scope_gives_fresh_service(validation_service):
    """
    validation_service is function-scoped (default), so this test starts
    with calls == 0 even though previous tests also used the service.
    """
    assert validation_service.calls == 0
    validation_service.validate({"id": 1, "name": "A", "email": "a@b.com"}, "user")
    assert validation_service.calls == 1


def test_module_scope_resource_is_shared_a(expensive_resource):
    """First test to use expensive_resource — triggers fixture setup."""
    assert "connection" in expensive_resource
    expensive_resource["counter"] = 1    # mutate to prove sharing


def test_module_scope_resource_is_shared_b(expensive_resource):
    """
    Same fixture instance as the test above (scope="module").
    The mutation from the previous test is visible here.
    """
    assert expensive_resource["connection"] == "mock-db-conn"
    assert expensive_resource.get("counter") == 1   # set by previous test


# ══════════════════════════════════════════════════════════════════════════════
# DEMO: scope reference table
# ══════════════════════════════════════════════════════════════════════════════

def demo_scope_table() -> None:
    print("\n" + "═" * 78)
    print("  PYTEST FIXTURE SCOPES")
    print("═" * 78)
    print()
    rows = [
        ("function", "default — no declaration",  "one per test call",          "max isolation"),
        ("class",    "scope='class'",              "shared within one class",    "moderate"),
        ("module",   "scope='module'",             "one per .py file",           "DB connection"),
        ("session",  "scope='session'",            "one per pytest run",         "expensive global"),
    ]
    print(f"  {'Scope':<10}  {'Declaration':<24}  {'Lifetime':<28}  Use for")
    print(f"  {'-'*10}  {'-'*24}  {'-'*28}  {'-'*20}")
    for scope, decl, lifetime, use in rows:
        print(f"  {scope:<10}  {decl:<24}  {lifetime:<28}  {use}")
    print()
    print("  conftest.py: place shared fixtures here; pytest auto-discovers, no import needed.")
    print()


def main() -> None:
    demo_scope_table()

    print("═" * 78)
    print("  RUNNING FIXTURE TESTS  (-s shows fixture print statements)")
    print("═" * 78)
    print()
    ret = pytest.main([__file__, "-v", "--tb=short", "--no-header", "-s"])
    sys.exit(ret)


if __name__ == "__main__":
    main()

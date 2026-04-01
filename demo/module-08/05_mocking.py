"""
05_mocking.py
=============
Replacing external dependencies with controlled fakes.

Topics:
  1. Why mock: speed, determinism, isolation
  2. mocker.patch.object() — patch a method on an existing object
  3. return_value — fixed response; side_effect — exception or sequence
  4. Asserting call count and arguments
  5. Cache-aside pattern: verify DB is skipped on cache hit

Run:
    python demo/module-08/05_mocking.py
    pytest demo/module-08/05_mocking.py -v
"""

import sys
from dataclasses import dataclass
from typing import Optional

import pytest


# ══════════════════════════════════════════════════════════════════════════════
# EXTERNAL DEPENDENCY — the component we will mock in tests
#
# In production this class opens a real DB connection.
# Tests must NOT hit the real DB: it's slow, non-deterministic, and requires
# infrastructure.  We mock it so tests run in milliseconds with no setup.
# ══════════════════════════════════════════════════════════════════════════════

class SchemaDB:
    """Simulates a slow schema registry backed by a database."""

    def fetch_schema(self, schema_name: str) -> dict:
        """Real call costs ~200ms round trip — tests must not reach this."""
        import time
        time.sleep(0.2)                              # ← slow; mock replaces this
        return {"name": schema_name, "fields": ["id", "name"]}

    def list_schemas(self) -> list[str]:
        import time
        time.sleep(0.1)
        return ["user", "product", "order"]


# ── module-level singleton that production code calls ──────────────────────
_db = SchemaDB()


# ══════════════════════════════════════════════════════════════════════════════
# PRODUCTION CODE that depends on the DB
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class ValidationResult:
    is_valid: bool
    error: Optional[str] = None


def validate_with_schema(record: dict, schema_name: str) -> ValidationResult:
    """Validates a record against a schema fetched from the registry."""
    try:
        schema = _db.fetch_schema(schema_name)
    except ConnectionError as e:
        return ValidationResult(False, f"schema unavailable: {e}")
    required = schema.get("fields", [])
    missing  = [f for f in required if f not in record]
    if missing:
        return ValidationResult(False, f"missing fields: {missing}")
    return ValidationResult(True)


def get_with_cache(key: str, cache: dict, fetch_fn) -> dict:
    """Cache-aside: return cached value if present, otherwise call fetch_fn."""
    if key in cache:
        return cache[key]
    value = fetch_fn(key)
    cache[key] = value
    return value


# ══════════════════════════════════════════════════════════════════════════════
# TESTS
#
# mocker.patch.object(obj, "method_name") replaces obj.method_name with a Mock
# for the duration of the test, then restores it automatically.
#
# This avoids the string-path fragility of mocker.patch("module.function"):
#   - Works regardless of how the module is imported
#   - Fails loudly if the attribute name is misspelled
# ══════════════════════════════════════════════════════════════════════════════

def test_valid_record_passes(mocker):
    """Happy path: DB returns a schema, record has all required fields."""
    mock_fetch = mocker.patch.object(_db, "fetch_schema")
    mock_fetch.return_value = {"name": "user", "fields": ["id", "name"]}

    result = validate_with_schema({"id": 1, "name": "Alice"}, "user")

    # assert behavior: DB was consulted once with the right schema name
    mock_fetch.assert_called_once_with("user")
    assert result.is_valid


def test_missing_required_field_fails(mocker):
    """Record is missing 'email' — validation must fail."""
    mock_fetch = mocker.patch.object(_db, "fetch_schema")
    mock_fetch.return_value = {"name": "user", "fields": ["id", "name", "email"]}

    result = validate_with_schema({"id": 1, "name": "Alice"}, "user")   # no email

    assert not result.is_valid
    assert "email" in result.error


def test_db_connection_error_degrades_gracefully(mocker):
    """DB raises ConnectionError — service returns invalid result, does not crash."""
    mock_fetch = mocker.patch.object(_db, "fetch_schema")
    mock_fetch.side_effect = ConnectionError("database unreachable")

    result = validate_with_schema({"id": 1}, "user")

    assert not result.is_valid
    assert "schema unavailable" in result.error


def test_cache_hit_skips_db():
    """Cache already has the value — fetch_fn must NOT be called."""
    mock_fetch = pytest.importorskip("unittest.mock").MagicMock(
        return_value={"fields": ["id"]}
    )
    cache = {"user": {"fields": ["id", "name"]}}   # pre-populated

    result = get_with_cache("user", cache, mock_fetch)

    mock_fetch.assert_not_called()       # ← the key assertion
    assert result == {"fields": ["id", "name"]}


def test_cache_miss_calls_db_once_and_populates(mocker):
    """Cache miss: fetch_fn called exactly once; second call uses cache."""
    from unittest.mock import MagicMock
    mock_fetch = MagicMock(return_value={"fields": ["id", "name"]})
    cache = {}

    get_with_cache("user", cache, mock_fetch)    # miss — calls DB
    get_with_cache("user", cache, mock_fetch)    # hit  — uses cache

    mock_fetch.assert_called_once_with("user")   # DB hit exactly once
    assert "user" in cache


def test_side_effect_sequence(mocker):
    """Mock returns different values on successive calls (side_effect as list)."""
    mock_fetch = mocker.patch.object(_db, "fetch_schema")
    mock_fetch.side_effect = [
        {"name": "user", "fields": ["id"]},               # call 1 → success
        ConnectionError("transient failure"),               # call 2 → raises
        {"name": "user", "fields": ["id", "name"]},        # call 3 → success
    ]

    r1 = validate_with_schema({"id": 1},             "user")
    r2 = validate_with_schema({"id": 2},             "user")
    r3 = validate_with_schema({"id": 3, "name": "X"}, "user")

    assert r1.is_valid           # fields=["id"], only "id" required
    assert not r2.is_valid       # ConnectionError → degraded
    assert r3.is_valid           # fields=["id","name"], both present
    assert mock_fetch.call_count == 3


def test_assert_call_args(mocker):
    """Inspect exactly what arguments the mock was called with."""
    mock_fetch = mocker.patch.object(_db, "fetch_schema")
    mock_fetch.return_value = {"name": "product", "fields": ["id", "name"]}

    validate_with_schema({"id": 1, "name": "Widget"}, "product")

    call = mock_fetch.call_args
    assert call.args == ("product",)    # positional arguments
    # assert call.kwargs == {}          # no keyword args in this call


# ══════════════════════════════════════════════════════════════════════════════
# DEMO: mock API reference
# ══════════════════════════════════════════════════════════════════════════════

def demo_mock_api() -> None:
    print("\n" + "═" * 78)
    print("  MOCKING API REFERENCE")
    print("═" * 78)
    print()
    print("  mocker.patch.object(obj, 'method')   → safest; no string path needed")
    print("  mocker.patch('pkg.module.function')  → patches by full import path")
    print()
    rows = [
        ("mock.return_value = X",          "always return X"),
        ("mock.side_effect = Exception()", "always raise this exception"),
        ("mock.side_effect = [a, b, c]",   "return a on 1st call, b on 2nd, …"),
        ("mock.assert_called_once_with(X)","assert called exactly once with arg X"),
        ("mock.assert_not_called()",       "assert never called"),
        ("mock.call_count",                "number of times called"),
        ("mock.call_args.args",            "positional args of the last call"),
        ("mock.call_args.kwargs",          "keyword args of the last call"),
    ]
    print(f"  {'API':<40}  Effect")
    print(f"  {'-'*40}  {'-'*36}")
    for api, effect in rows:
        print(f"  {api:<40}  {effect}")
    print()
    print("  Patch target rule: patch WHERE the name is USED, not where defined.")
    print("  If service.py does `from db import get_user`,")
    print("  patch 'service.get_user', not 'db.get_user'.")
    print()


def main() -> None:
    demo_mock_api()

    print("═" * 78)
    print("  RUNNING MOCK TESTS")
    print("═" * 78)
    print()
    ret = pytest.main([__file__, "-v", "--tb=short", "--no-header"])
    sys.exit(ret)


if __name__ == "__main__":
    main()

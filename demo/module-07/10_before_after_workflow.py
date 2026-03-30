"""
10_before_after_workflow.py
=============================
The complete performance engineering workflow from start to finish.

Demonstrates the full cycle on a realistic validation service:
  Step 1: Define the target (SLA)
  Step 2: Establish baseline with timeit
  Step 3: Profile with cProfile — find the top 3 hotspots
  Step 4: Fix hotspot #1 (regex re-compile)
  Step 5: Re-measure — confirm improvement
  Step 6: Profile again — find hotspot #2 (repeated schema load)
  Step 7: Fix hotspot #2 (lru_cache)
  Step 8: Final benchmark — report speedup and SLA status

Run:
    python demo/module-07/10_before_after_workflow.py
"""

import cProfile
import pstats
import io
import re
import time
import timeit
from functools import lru_cache


# ══════════════════════════════════════════════════════════════════════════════
# The validation service — three versions
#
# v1: Original (two deliberate bottlenecks)
# v2: Fix #1 applied (regex pre-compiled)
# v3: Fix #1 + Fix #2 applied (regex + lru_cache)
# ══════════════════════════════════════════════════════════════════════════════

# ------ Shared simulated database -----------------------------------------

_SCHEMA_DB = {
    "user":    {"fields": ["email", "name", "age"], "required": ["email", "name"]},
    "product": {"fields": ["sku", "price", "category"], "required": ["sku"]},
    "order":   {"fields": ["order_id", "user_id", "total"], "required": ["order_id"]},
}


# ------ VERSION 1: Original (no optimizations) ----------------------------

def load_schema_v1(schema_name: str) -> dict:
    """V1: Expensive schema lookup — 0.2ms per call, no caching."""
    time.sleep(0.0002)
    return _SCHEMA_DB.get(schema_name, {})


def validate_record_v1(record: dict) -> bool:
    """V1: Two bottlenecks — re.fullmatch raw string + load_schema per record."""
    schema = load_schema_v1(record.get("schema", "user"))

    email = record.get("email", "")
    valid_email = re.fullmatch(                   # BOTTLENECK: re-compile each call
        r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
        email,
    ) is not None

    required = schema.get("required", [])
    has_required = all(record.get(f) for f in required)

    return valid_email and has_required


def validate_batch_v1(records: list[dict]) -> list[bool]:
    return [validate_record_v1(r) for r in records]


# ------ VERSION 2: Fix #1 — pre-compiled regex ----------------------------

_EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")


def validate_record_v2(record: dict) -> bool:
    """V2: Pre-compiled regex. load_schema still called per record."""
    schema = load_schema_v1(record.get("schema", "user"))   # still slow

    email = record.get("email", "")
    valid_email = _EMAIL_RE.fullmatch(email) is not None    # FIX #1 applied

    required = schema.get("required", [])
    has_required = all(record.get(f) for f in required)

    return valid_email and has_required


def validate_batch_v2(records: list[dict]) -> list[bool]:
    return [validate_record_v2(r) for r in records]


# ------ VERSION 3: Fix #1 + Fix #2 — lru_cache for schema loading ---------

@lru_cache(maxsize=32)
def load_schema_v3(schema_name: str) -> tuple:
    """V3: Cached schema load — 0.2ms only on first call per schema name.
    Returns a tuple (required_fields...) because dicts are not hashable
    and lru_cache requires hashable return values for the cache.
    Actually we just cache the dict — the tuple is the key.
    """
    time.sleep(0.0002)
    schema = _SCHEMA_DB.get(schema_name, {})
    return schema.get("required", [])


def validate_record_v3(record: dict) -> bool:
    """V3: Pre-compiled regex + cached schema load — both hotspots fixed."""
    required = load_schema_v3(record.get("schema", "user"))  # FIX #2 applied

    email = record.get("email", "")
    valid_email = _EMAIL_RE.fullmatch(email) is not None     # FIX #1

    has_required = all(record.get(f) for f in required)

    return valid_email and has_required


def validate_batch_v3(records: list[dict]) -> list[bool]:
    return [validate_record_v3(r) for r in records]


# ------ Test records -------------------------------------------------------

def make_records(n: int) -> list[dict]:
    schemas = ["user", "product", "order"]
    return [
        {
            "email":  f"user{i}@example.com",
            "name":   f"User {i}",
            "schema": schemas[i % len(schemas)],
        }
        for i in range(n)
    ]


# ══════════════════════════════════════════════════════════════════════════════
# The workflow
# ══════════════════════════════════════════════════════════════════════════════

def profile_batch(batch_fn, records, label: str, n_print: int = 8) -> None:
    profiler = cProfile.Profile()
    profiler.enable()
    batch_fn(records)
    profiler.disable()

    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.strip_dirs()
    stats.sort_stats("tottime")
    stats.print_stats(n_print)
    raw = stream.getvalue()

    print(f"\n  Profile ({label}) — top {n_print} by tottime:")
    for line in raw.splitlines():
        if any(x in line for x in [
            "validate", "load_schema", "fullmatch", "sleep",
            "compile", "ncalls", "tottime"
        ]):
            print(f"    {line}")


def benchmark(batch_fn, records, number: int = 5) -> float:
    """Returns min per-call ms over 3 repeats."""
    return min(timeit.repeat(lambda: batch_fn(records), number=number, repeat=3)) / number * 1000


def run_workflow():
    RECORDS = make_records(500)     # 500 records, 3 distinct schemas
    SLA_MS  = 10.0                  # target: < 10ms per batch of 500 records

    print("╔" + "═" * 62 + "╗")
    print("║  PERFORMANCE ENGINEERING WORKFLOW                            ║")
    print("╚" + "═" * 62 + "╝")

    # ── STEP 1: Define the target ──────────────────────────────────────────
    print()
    print("  STEP 1: Define the target")
    print(f"    Batch size: {len(RECORDS):,} records")
    print(f"    SLA:        batch must complete in < {SLA_MS}ms")
    print()

    # ── STEP 2: Baseline measurement ───────────────────────────────────────
    print("  STEP 2: Establish baseline (v1 — no optimizations)")
    baseline_ms = benchmark(validate_batch_v1, RECORDS, number=3)
    status = "✓ PASS" if baseline_ms < SLA_MS else "✗ FAIL"
    print(f"    Baseline: {baseline_ms:.1f}ms  {status}")

    # ── STEP 3: Profile v1 ─────────────────────────────────────────────────
    print()
    print("  STEP 3: Profile v1 — find hotspots")
    profile_batch(validate_batch_v1, RECORDS, "v1 — no optimizations")
    print()
    print("    Hotspot #1: re.fullmatch / re._compile   → ncalls = batch_size")
    print("    Hotspot #2: load_schema_v1 / sleep       → ncalls = batch_size")
    print("    Fix order:  apply the biggest cumtime fix first")

    # ── STEP 4: Fix #1 — pre-compile regex ────────────────────────────────
    print()
    print("  STEP 4: Apply fix #1 — pre-compile regex at module level")
    v2_ms = benchmark(validate_batch_v2, RECORDS, number=3)
    speedup_v2 = baseline_ms / v2_ms
    status = "✓ PASS" if v2_ms < SLA_MS else "✗ FAIL"
    print(f"    v2 (regex fix):  {v2_ms:.1f}ms  {status}  ({speedup_v2:.1f}× over baseline)")

    # Verify correctness
    assert validate_batch_v1(RECORDS) == validate_batch_v2(RECORDS), "v1 vs v2 mismatch"
    print(f"    Correctness: ✓")

    # ── STEP 5: Profile v2 ─────────────────────────────────────────────────
    print()
    print("  STEP 5: Profile v2 — regex gone, what's next?")
    profile_batch(validate_batch_v2, RECORDS, "v2 — regex fixed")
    print()
    print("    Hotspot #1 (re.fullmatch) is gone.")
    print("    Hotspot #2 (load_schema / sleep) is now the top entry.")

    # ── STEP 6: Fix #2 — lru_cache for schema loading ─────────────────────
    print()
    print("  STEP 6: Apply fix #2 — @lru_cache on load_schema")
    load_schema_v3.cache_clear()    # ensure cold cache for first-run accuracy
    # Warm cache for benchmark
    for r in RECORDS:
        load_schema_v3(r.get("schema", "user"))

    v3_ms = benchmark(validate_batch_v3, RECORDS, number=5)
    speedup_v3 = baseline_ms / v3_ms
    status = "✓ PASS" if v3_ms < SLA_MS else "✗ FAIL"
    print(f"    v3 (regex + cache):  {v3_ms:.2f}ms  {status}  ({speedup_v3:.0f}× over baseline)")

    # Verify correctness
    assert validate_batch_v1(RECORDS) == validate_batch_v3(RECORDS), "v1 vs v3 mismatch"
    print(f"    Correctness: ✓")

    cache_info = load_schema_v3.cache_info()
    print(f"    Cache: hits={cache_info.hits}  misses={cache_info.misses}  "
          f"(3 misses = 3 distinct schemas)")

    # ── STEP 7: Profile v3 ─────────────────────────────────────────────────
    print()
    print("  STEP 7: Profile v3 — confirm both hotspots eliminated")
    profile_batch(validate_batch_v3, RECORDS, "v3 — both fixes applied")

    # ── STEP 8: Final report ───────────────────────────────────────────────
    print()
    print("  " + "═" * 60)
    print("  FINAL REPORT")
    print("  " + "═" * 60)
    print()
    print(f"  {'Version':<20}  {'Time':>8}  {'vs Baseline':>12}  {'SLA':>6}")
    print(f"  {'─'*20}  {'─'*8}  {'─'*12}  {'─'*6}")

    versions = [
        ("v1 (original)",        baseline_ms, "—"),
        ("v2 (regex fix)",       v2_ms,        f"{speedup_v2:.1f}×"),
        ("v3 (regex + cache)",   v3_ms,        f"{speedup_v3:.0f}×"),
    ]
    for name, ms, speedup in versions:
        s = "✓" if ms < SLA_MS else "✗"
        print(f"  {name:<20}  {ms:>7.2f}ms  {speedup:>12}  {s}")

    print()
    print("  Total improvement achieved with 2 targeted changes:")
    print(f"    1. Move re.compile() to module level")
    print(f"    2. Add @lru_cache(maxsize=32) to load_schema")
    print()
    print("  Methodology: profile → identify #1 hotspot → fix → re-profile → repeat.")
    print("  NEVER fix both at once — you can't measure the contribution of each.")


def main():
    run_workflow()


if __name__ == "__main__":
    main()

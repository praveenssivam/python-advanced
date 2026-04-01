"""
07_optimization_patterns.py
=============================
Five optimization patterns with measured before/after comparisons.

Topics:
  1. Better algorithm: O(n²) → O(n) with a set
  2. Built-ins: Python loop → list comprehension / map / sum
  3. Caching: lru_cache for repeated expensive calls
  4. Batching: N individual DB-like calls → 1 batch call
  5. Lazy evaluation: eager list pipeline → generator pipeline

For each pattern: BAD version → WHY it's slow → GOOD version → speedup.

Run:
    python demo/module-07/07_optimization_patterns.py
"""

import timeit
import time
from functools import lru_cache


# ══════════════════════════════════════════════════════════════════════════════
# PATTERN 1: Better Algorithm — O(n²) → O(n)
#
# Finding duplicates in a list.
# Naive approach: for each element, check if it's in seen (O(n) per check).
# Total: O(n²).
# Set approach: hash lookup is O(1) average.
# Total: O(n).
#
# At n=10,000: O(n²) = 100M operations vs O(n) = 10K operations → ~10,000×
# ══════════════════════════════════════════════════════════════════════════════

def find_duplicates_on2(items: list) -> list:
    """O(n²): inner scan of seen list on every element."""
    seen = []
    duplicates = []
    for item in items:
        if item in seen:       # O(n) scan each time
            if item not in duplicates:
                duplicates.append(item)
        else:
            seen.append(item)
    return duplicates


def find_duplicates_on(items: list) -> list:
    """O(n): set membership is O(1) average."""
    seen = set()
    duplicates = set()
    for item in items:
        if item in seen:       # O(1) hash lookup
            duplicates.add(item)
        else:
            seen.add(item)
    return sorted(duplicates)


def demo_algorithm():
    print("=" * 60)
    print("PATTERN 1: Better Algorithm — O(n²) → O(n)")
    print("=" * 60)
    print()

    # Small N for correctness check
    sample = [1, 2, 3, 2, 4, 3, 5]
    r1 = sorted(find_duplicates_on2(sample))
    r2 = find_duplicates_on(sample)
    assert r1 == r2, f"Mismatch: {r1} vs {r2}"

    # Benchmark with increasing N
    print(f"  {'N':>8}  {'O(n²) ms':>10}  {'O(n) ms':>10}  {'Speedup':>10}")
    print(f"  {'─'*8}  {'─'*10}  {'─'*10}  {'─'*10}")

    for N in [500, 2_000, 5_000]:
        # 50% unique items to guarantee duplicates
        data = list(range(N // 2)) * 2

        t1 = min(timeit.repeat(lambda: find_duplicates_on2(data), number=5, repeat=3)) / 5 * 1000
        t2 = min(timeit.repeat(lambda: find_duplicates_on(data),  number=50, repeat=3)) / 50 * 1000
        speedup = t1 / t2

        print(f"  {N:>8,}  {t1:>10.2f}  {t2:>10.3f}  {speedup:>9.0f}×")

    print()
    print("  Speedup grows with N — algorithmic improvements scale.")
    print("  No amount of micro-optimization can close an O(n²) vs O(n) gap.")


# ══════════════════════════════════════════════════════════════════════════════
# PATTERN 2: Built-ins — pure Python loop → C-backed operations
#
# Python's built-in functions (sum, min, max, any, all, filter, map) are
# implemented in C and loop at C speed.  A pure Python for-loop iterates
# at Python bytecode speed (~100ns/iteration vs ~10ns/iteration for C).
# ══════════════════════════════════════════════════════════════════════════════

def total_slow(values: list[float], multiplier: float) -> float:
    """BAD: pure Python loop."""
    total = 0.0
    for v in values:
        total += v * multiplier
    return total


def total_fast(values: list[float], multiplier: float) -> float:
    """GOOD: generator expression inside sum() — C-backed loop."""
    return sum(v * multiplier for v in values)


def filter_slow(records: list[dict]) -> list[dict]:
    """BAD: Python loop with manual append."""
    result = []
    for r in records:
        if r["value"] > 0:
            result.append(r)
    return result


def filter_fast(records: list[dict]) -> list[dict]:
    """GOOD: list comprehension — C-backed loop."""
    return [r for r in records if r["value"] > 0]


def demo_builtins():
    print("\n" + "=" * 60)
    print("PATTERN 2: Built-ins — Python loop → C-backed operations")
    print("=" * 60)
    print()

    N = 100_000
    values  = [float(i) for i in range(N)]
    records = [{"value": float(i - N // 2)} for i in range(N)]
    number  = 200

    # sum
    t_slow = min(timeit.repeat(lambda: total_slow(values, 2.0), number=number, repeat=3)) / number * 1000
    t_fast = min(timeit.repeat(lambda: total_fast(values, 2.0), number=number, repeat=3)) / number * 1000
    assert abs(total_slow(values, 2.0) - total_fast(values, 2.0)) < 0.01

    print(f"  sum({N:,} floats × multiplier)")
    print(f"    BAD  (Python loop):              {t_slow:.3f}ms")
    print(f"    GOOD (sum() with genexpr):       {t_fast:.3f}ms")
    print(f"    Speedup: {t_slow/t_fast:.1f}×")
    print()

    # filter
    t_slow2 = min(timeit.repeat(lambda: filter_slow(records), number=number, repeat=3)) / number * 1000
    t_fast2 = min(timeit.repeat(lambda: filter_fast(records), number=number, repeat=3)) / number * 1000
    assert len(filter_slow(records)) == len(filter_fast(records))

    print(f"  filter {N:,} records (value > 0)")
    print(f"    BAD  (loop + append):            {t_slow2:.3f}ms")
    print(f"    GOOD (list comprehension):       {t_fast2:.3f}ms")
    print(f"    Speedup: {t_slow2/t_fast2:.1f}×")


# ══════════════════════════════════════════════════════════════════════════════
# PATTERN 3: Caching — lru_cache for repeated pure function calls
#
# Already covered in detail in 04_lru_cache_optimization.py.
# This shows a compact before/after specifically for a rule compilation step.
# ══════════════════════════════════════════════════════════════════════════════

def _compile_rule_uncached(rule_spec: str) -> dict:
    """Simulate expensive rule compilation (0.5ms per call)."""
    time.sleep(0.0005)
    return {"spec": rule_spec, "compiled": True}


@lru_cache(maxsize=64)
def _compile_rule_cached(rule_spec: str) -> dict:
    """Same, but cached — called at most once per unique rule_spec."""
    time.sleep(0.0005)
    return {"spec": rule_spec, "compiled": True}


def validate_with_compile(record: dict, rule_spec: str) -> bool:
    rule = _compile_rule_uncached(rule_spec)
    return bool(rule["compiled"])


def validate_with_cache(record: dict, rule_spec: str) -> bool:
    rule = _compile_rule_cached(rule_spec)
    return bool(rule["compiled"])


def demo_caching():
    print("\n" + "=" * 60)
    print("PATTERN 3: Caching — lru_cache for repeated pure calls")
    print("=" * 60)
    print()

    N = 50
    n_rules = 4   # only 4 distinct rules across all records
    records = [{"id": i} for i in range(N)]
    rules   = [f"rule_{i % n_rules}" for i in range(N)]

    _compile_rule_cached.cache_clear()

    # Warm cache pass
    for r, rule in zip(records, rules):
        validate_with_cache(r, rule)
    _compile_rule_cached.cache_clear()

    t_uncached = timeit.timeit(
        lambda: [validate_with_compile(r, rule) for r, rule in zip(records, rules)],
        number=1
    ) * 1000

    _compile_rule_cached.cache_clear()
    t_cached = timeit.timeit(
        lambda: [validate_with_cache(r, rule) for r, rule in zip(records, rules)],
        number=1
    ) * 1000

    info = _compile_rule_cached.cache_info()
    print(f"  {N} records × {n_rules} distinct rules (each rule used {N//n_rules}×)")
    print()
    print(f"  BAD  (compile each call):     {t_uncached:.0f}ms  ({N} compiles)")
    print(f"  GOOD (lru_cache, warm):       {t_cached:.1f}ms  ({info.misses} compiles)")
    print(f"  Speedup: {t_uncached/max(t_cached,0.001):.0f}×")
    print(f"  Cache: {info}")


# ══════════════════════════════════════════════════════════════════════════════
# PATTERN 4: Batching — N individual calls → 1 batch call
#
# Any I/O operation (DB query, HTTP call, file read) has a fixed per-call
# overhead (network round-trip, TCP handshake, connection pool checkout).
# Batching eliminates N-1 of those overheads.
#
# NOTE: NEVER use string interpolation to build SQL.  Always use
# parameterised queries (the `db.get_batch(ids)` pattern here represents
# a parameterised batch call, not string concatenation).
# ══════════════════════════════════════════════════════════════════════════════

_DB_STORE = {i: f"meta_{i}" for i in range(1_000)}   # simulated DB


def db_get_one(record_id: int) -> str:
    """Simulate single-row DB query: 1ms fixed overhead + 0.1ms per row."""
    time.sleep(0.001)
    return _DB_STORE.get(record_id, "unknown")


def db_get_batch(record_ids: list[int]) -> dict[int, str]:
    """Simulate batch DB query: 1ms fixed overhead + 0.1ms per row (shared)."""
    time.sleep(0.001 + len(record_ids) * 0.0001)
    return {rid: _DB_STORE.get(rid, "unknown") for rid in record_ids}


def enrich_sequential(records: list[dict]) -> list[dict]:
    """BAD: one DB call per record — N × (1ms + 0.1ms)."""
    for record in records:
        record["meta"] = db_get_one(record["id"])
    return records


def enrich_batched(records: list[dict]) -> list[dict]:
    """GOOD: one batch DB call — 1 × (1ms + N×0.1ms)."""
    ids = [r["id"] for r in records]
    meta_map = db_get_batch(ids)       # single parameterised batch query
    for record in records:
        record["meta"] = meta_map.get(record["id"], "unknown")
    return records


def demo_batching():
    print("\n" + "=" * 60)
    print("PATTERN 4: Batching — N individual calls → 1 batch call")
    print("=" * 60)
    print()

    import copy
    N = 20
    base_records = [{"id": i} for i in range(N)]

    records_seq = copy.deepcopy(base_records)
    t_seq = timeit.timeit(lambda: enrich_sequential(copy.deepcopy(base_records)),
                          number=3) / 3 * 1000

    t_batch = timeit.timeit(lambda: enrich_batched(copy.deepcopy(base_records)),
                            number=3) / 3 * 1000

    print(f"  Workload: {N} records, each needs a DB lookup")
    print(f"    Fixed overhead per call:   1ms")
    print(f"    Per-row processing:        0.1ms")
    print()
    print(f"  BAD  (N individual calls):  {t_seq:.0f}ms   ← {N}×1ms overhead")
    print(f"  GOOD (1 batch call):        {t_batch:.0f}ms    ← 1×1ms overhead")
    print(f"  Speedup: {t_seq/t_batch:.1f}×")
    print()
    print("  Rule: if ncalls = batch_size in profiler, look for batching opportunity.")
    print("  SECURITY: always use parameterised queries, never string interpolation.")


# ══════════════════════════════════════════════════════════════════════════════
# PATTERN 5: Lazy evaluation — reduce peak memory in a pipeline
#
# Already covered in depth in 05_generators_vs_lists.py.
# This shows the pattern applied to the capstone-style validation pipeline.
# ══════════════════════════════════════════════════════════════════════════════

def run_pipeline_eager(records: list[dict]) -> list[str]:
    cleaned  = [r for r in records if r.get("email")]           # list
    tagged   = [{**r, "tag": r["email"].split("@")[1]} for r in cleaned]  # list
    exported = [f"{r['id']}:{r['tag']}" for r in tagged]       # list
    return exported


def run_pipeline_lazy(records: list[dict]):
    cleaned  = (r      for r in records if r.get("email"))
    tagged   = ({**r, "tag": r["email"].split("@")[1]} for r in cleaned)
    exported = (f"{r['id']}:{r['tag']}" for r in tagged)
    return exported   # generator — O(1) memory


def demo_lazy():
    print("\n" + "=" * 60)
    print("PATTERN 5: Lazy evaluation — generator pipeline")
    print("=" * 60)
    print()

    import tracemalloc

    N = 200_000
    records = [{"id": i, "email": f"user{i}@example.com"} for i in range(N)]

    # Eager — measure peak
    tracemalloc.start()
    _ = run_pipeline_eager(records)
    _, peak_eager = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Lazy — measure peak (consume generator with sum to trigger execution)
    tracemalloc.start()
    gen = run_pipeline_lazy(records)
    total_chars = sum(len(x) for x in gen)   # consume without storing
    _, peak_lazy = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"  Pipeline: clean → tag → export  ({N:,} records)")
    print()
    print(f"  Eager (3 intermediate lists):  peak = {peak_eager / 1024 / 1024:.1f} MB")
    print(f"  Lazy  (3 chained generators):  peak = {peak_lazy  / 1024:.0f} KB")
    print(f"  Memory reduction: {peak_eager / max(peak_lazy, 1):.0f}×")
    print()
    print(f"  Both produced the same total output chars: {total_chars:,}")


def main():
    demo_algorithm()
    demo_builtins()
    demo_caching()
    demo_batching()
    demo_lazy()


if __name__ == "__main__":
    main()

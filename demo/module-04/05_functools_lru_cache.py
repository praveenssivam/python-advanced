"""
05_functools_lru_cache.py
===========================
functools.lru_cache(maxsize=N) memoises a function's return values.

On the first call for a given set of arguments: execute the function
and store the result in a cache keyed by the arguments.
On subsequent calls with the same arguments: return the cached result
without calling the function at all.

"LRU" = Least Recently Used — when the cache is full, the entry that
was accessed longest ago is evicted to make room.

Run:
    python demo/module-04/05_functools_lru_cache.py
"""

import time
from functools import lru_cache


# ══════════════════════════════════════════════════════════════════════════════
# PART 1: Basic caching — cache hits avoid re-computation
#
# Flow for @lru_cache on expensive_compute(n):
#
#   expensive_compute(5)            ← first call
#     → not in cache
#     → execute function body (slow)
#     → store result in cache[5]
#     → return result
#
#   expensive_compute(5)            ← second call
#     → cache[5] exists             ← CACHE HIT
#     → return cached result immediately (no function body runs)
#
#   expensive_compute.cache_info()  ← inspect the cache
#     → CacheInfo(hits=1, misses=1, maxsize=128, currsize=1)
# ══════════════════════════════════════════════════════════════════════════════

@lru_cache(maxsize=128)
def expensive_compute(n: int) -> int:
    """Simulate an expensive computation. Prints when it actually runs."""
    print(f"  [COMPUTING] expensive_compute({n}) ← function body executing")
    time.sleep(0.05)    # simulate latency
    return n * n + n + 1


def demo_basic_cache():
    print("=" * 55)
    print("PART 1: Cache hits — function body only runs once per unique arg")
    print("=" * 55)
    print()

    print("Calling expensive_compute(7) three times:")
    r1 = expensive_compute(7)
    r2 = expensive_compute(7)   # cache hit — no print, no sleep
    r3 = expensive_compute(7)   # cache hit
    print(f"  Results: {r1}, {r2}, {r3}  (all equal: {r1 == r2 == r3})")

    print()
    print("Calling with different arguments:")
    expensive_compute(3)
    expensive_compute(5)
    expensive_compute(3)   # cache hit for 3

    print()
    print(f"Cache info: {expensive_compute.cache_info()}")
    print("  hits   = calls that returned the cached value")
    print("  misses = calls that had to execute the function")


# ══════════════════════════════════════════════════════════════════════════════
# PART 2: Classic example — Fibonacci
#
# Without caching, recursive fib(n) recomputes fib(k) many times.
# With lru_cache, each fib(k) is computed exactly once.
#
# Without cache: fib(30) makes ~2.7 million calls.
# With cache:    fib(30) makes exactly 31 calls (each k from 0..30 once).
# ══════════════════════════════════════════════════════════════════════════════

_call_count = {"no_cache": 0, "with_cache": 0}


def fib_no_cache(n: int) -> int:
    """Naive recursive Fibonacci — recomputes sub-problems every time."""
    _call_count["no_cache"] += 1
    if n < 2:
        return n
    return fib_no_cache(n - 1) + fib_no_cache(n - 2)


@lru_cache(maxsize=None)  # maxsize=None → unlimited cache (functools.cache equivalent)
def fib_cached(n: int) -> int:
    """Memoised Fibonacci — each sub-problem computed exactly once."""
    _call_count["with_cache"] += 1
    if n < 2:
        return n
    return fib_cached(n - 1) + fib_cached(n - 2)


def demo_fibonacci():
    print("\n" + "=" * 55)
    print("PART 2: Fibonacci — call count with and without cache")
    print("=" * 55)
    print()

    n = 25

    _call_count["no_cache"] = 0
    t0 = time.perf_counter()
    result_no_cache = fib_no_cache(n)
    t1 = time.perf_counter()

    _call_count["with_cache"] = 0
    t2 = time.perf_counter()
    result_with_cache = fib_cached(n)
    t3 = time.perf_counter()

    print(f"fib({n}) = {result_no_cache}")
    print()
    print(f"  Without cache: {_call_count['no_cache']:>7} function calls, "
          f"{(t1-t0)*1000:.1f} ms")
    print(f"  With cache:    {_call_count['with_cache']:>7} function calls, "
          f"{(t3-t2)*1000:.1f} ms")
    print()
    print(f"  Cache info: {fib_cached.cache_info()}")


# ══════════════════════════════════════════════════════════════════════════════
# PART 3: Practical use — caching schema lookups and config reads
#
# Any function whose output depends ONLY on its inputs (pure function)
# is a good candidate for lru_cache.
#
# Requirements for lru_cache:
#   - Arguments must be HASHABLE (no lists or dicts as args).
#   - The function must be PURE — same args always produce same result.
#   - Do NOT use on functions with side effects (file writes, DB state, etc.).
# ══════════════════════════════════════════════════════════════════════════════

@lru_cache(maxsize=32)
def get_column_schema(table_name: str, column: str) -> dict:
    """Simulate a slow schema lookup (DB or API call).

    In production this would query a metadata service.
    With caching, each (table, column) pair is looked up once per process.
    """
    print(f"  [SCHEMA LOOKUP] {table_name}.{column} ← executing")
    time.sleep(0.03)
    # Simulated schema registry
    schemas = {
        ("trips", "distance"):  {"type": "float",   "nullable": False},
        ("trips", "duration"):  {"type": "integer",  "nullable": False},
        ("trips", "pickup_at"): {"type": "datetime", "nullable": True},
    }
    return schemas.get((table_name, column), {"type": "unknown", "nullable": True})


def demo_schema_cache():
    print("\n" + "=" * 55)
    print("PART 3: Caching schema lookups")
    print("=" * 55)
    print()

    lookups = [
        ("trips", "distance"),
        ("trips", "duration"),
        ("trips", "distance"),   # cache hit
        ("trips", "pickup_at"),
        ("trips", "duration"),   # cache hit
        ("trips", "distance"),   # cache hit
    ]

    print("Schema lookup calls (watch for '[SCHEMA LOOKUP]' prints):")
    for table, col in lookups:
        schema = get_column_schema(table, col)
        print(f"  {table}.{col}: {schema}")

    print()
    print(f"Cache info: {get_column_schema.cache_info()}")
    print("  Only 3 actual lookups for 6 calls (3 were cache hits).")

    print()
    print("Clearing the cache (e.g. after schema change):")
    get_column_schema.cache_clear()
    print(f"  After clear: {get_column_schema.cache_info()}")


# ══════════════════════════════════════════════════════════════════════════════
# PART 4: maxsize and eviction
# ══════════════════════════════════════════════════════════════════════════════

@lru_cache(maxsize=3)
def compute_with_small_cache(n: int) -> int:
    print(f"  [COMPUTE] n={n}")
    return n * 10


def demo_maxsize():
    print("\n" + "=" * 55)
    print("PART 4: maxsize — LRU eviction")
    print("=" * 55)
    print()

    print("Cache with maxsize=3:")
    print("Calling with n=1,2,3 (fills cache):")
    for n in [1, 2, 3]:
        compute_with_small_cache(n)
    print(f"  Cache info: {compute_with_small_cache.cache_info()}")

    print()
    print("Calling n=4 (evicts least-recently-used entry = n=1):")
    compute_with_small_cache(4)
    print(f"  Cache info: {compute_with_small_cache.cache_info()}")

    print()
    print("Calling n=1 again (evicted — must recompute):")
    compute_with_small_cache(1)
    print(f"  Cache info: {compute_with_small_cache.cache_info()}")


def main():
    demo_basic_cache()
    demo_fibonacci()
    demo_schema_cache()
    demo_maxsize()


if __name__ == "__main__":
    main()

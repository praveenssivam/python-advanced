"""
04_lru_cache_optimization.py
=============================
Caching expensive repeated calls with functools.lru_cache.

Topics:
  1. Identifying repeated expensive calls via ncalls in profiler
  2. @lru_cache — usage, maxsize, typed
  3. Cache hit rate and cache_info()
  4. When NOT to use lru_cache

Run:
    python demo/module-07/04_lru_cache_optimization.py
"""

import cProfile
import pstats
import io
import time
import timeit
from functools import lru_cache


# ══════════════════════════════════════════════════════════════════════════════
# PART 1: The bottleneck — expensive function called with repeated inputs
#
# load_schema() simulates loading a JSON schema from disk (0.3ms per call).
# In a batch of 1,000 records, all of the same schema, this is called 1,000
# times — but the result is identical every time.
#
# Profile will show: ncalls = batch_size, tottime = batch_size × 0.3ms
# ══════════════════════════════════════════════════════════════════════════════

# Shared call counter so we can verify cache behaviour
_load_calls = {"count": 0}


def load_schema_uncached(schema_name: str) -> dict:
    """Simulate expensive schema load (0.3ms) — no caching."""
    _load_calls["count"] += 1
    time.sleep(0.0003)   # 0.3ms — simulate disk/parse
    return {
        "name": schema_name,
        "fields": ["email", "age", "country"],
        "version": "1.0",
    }


@lru_cache(maxsize=128)
def load_schema_cached(schema_name: str) -> dict:
    """
    Simulate expensive schema load — cached after first call per name.
    maxsize=128 means at most 128 distinct schema_name values are cached.
    """
    _load_calls["count"] += 1
    time.sleep(0.0003)
    return {
        "name": schema_name,
        "fields": ["email", "age", "country"],
        "version": "1.0",
    }


def validate_uncached(record: dict) -> bool:
    schema = load_schema_uncached(record["schema"])
    return record.get("email", "").count("@") == 1


def validate_cached(record: dict) -> bool:
    schema = load_schema_cached(record["schema"])
    return record.get("email", "").count("@") == 1


def make_records(n: int, n_schemas: int = 3) -> list[dict]:
    """Create n records spread across n_schemas distinct schemas."""
    schemas = [f"schema_{i % n_schemas}" for i in range(n)]
    return [
        {"email": f"user{i}@example.com", "schema": schemas[i]}
        for i in range(n)
    ]


# ══════════════════════════════════════════════════════════════════════════════
# PART 2: Profile the uncached version — see ncalls = batch_size
# ══════════════════════════════════════════════════════════════════════════════

def demo_profile_uncached():
    print("=" * 60)
    print("PART 1: Profile — load_schema called once per record (no cache)")
    print("=" * 60)
    print()

    records = make_records(100, n_schemas=3)
    _load_calls["count"] = 0

    profiler = cProfile.Profile()
    profiler.enable()
    [validate_uncached(r) for r in records]
    profiler.disable()

    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.strip_dirs()
    stats.sort_stats("tottime")
    stats.print_stats(8)
    raw = stream.getvalue()

    print(f"  Batch: {len(records)} records using 3 distinct schemas")
    print(f"  load_schema actual calls: {_load_calls['count']}")
    print()
    print("  Profile output (tottime sorted):")
    for line in raw.splitlines():
        if any(x in line for x in ["load_schema", "sleep", "ncalls"]):
            print(f"    {line}")
    print()
    print(f"  Observation: load_schema_uncached called {len(records)} times.")
    print(f"  But there are only 3 distinct schemas — 97 calls are redundant.")
    print(f"  Fix: cache the result per schema_name.")


# ══════════════════════════════════════════════════════════════════════════════
# PART 3: Profile the cached version — ncalls drops to n_distinct_schemas
# ══════════════════════════════════════════════════════════════════════════════

def demo_profile_cached():
    print("\n" + "=" * 60)
    print("PART 2: Profile — load_schema_cached (lru_cache)")
    print("=" * 60)
    print()

    records = make_records(100, n_schemas=3)
    load_schema_cached.cache_clear()   # start fresh
    _load_calls["count"] = 0

    profiler = cProfile.Profile()
    profiler.enable()
    [validate_cached(r) for r in records]
    profiler.disable()

    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.strip_dirs()
    stats.sort_stats("tottime")
    stats.print_stats(8)
    raw = stream.getvalue()

    info = load_schema_cached.cache_info()

    print(f"  Batch: {len(records)} records using 3 distinct schemas")
    print(f"  load_schema actual calls: {_load_calls['count']}  ← only unique schemas")
    print()
    print(f"  Cache stats: hits={info.hits}  misses={info.misses}  "
          f"size={info.currsize}  maxsize={info.maxsize}")
    print(f"  Hit rate: {info.hits / (info.hits + info.misses):.0%}")
    print()
    print("  Profile output (tottime sorted):")
    for line in raw.splitlines():
        if any(x in line for x in ["load_schema", "sleep", "ncalls"]):
            print(f"    {line}")
    print()
    print(f"  Observation: load_schema_cached only called {_load_calls['count']} times.")
    print(f"  Remaining {len(records) - _load_calls['count']} calls are instant cache hits.")


# ══════════════════════════════════════════════════════════════════════════════
# PART 4: Benchmark — how much faster is the cached version?
# ══════════════════════════════════════════════════════════════════════════════

def demo_benchmark():
    print("\n" + "=" * 60)
    print("PART 3: Benchmark — before vs after caching")
    print("=" * 60)
    print()

    records = make_records(200, n_schemas=3)
    number = 3   # small number — each run takes ~60ms uncached

    slow_times = timeit.repeat(lambda: [validate_uncached(r) for r in records],
                               number=number, repeat=3)

    # Warm the cache once before timing
    load_schema_cached.cache_clear()
    [validate_cached(r) for r in records]   # warm
    fast_times = timeit.repeat(lambda: [validate_cached(r) for r in records],
                               number=number, repeat=3)

    slow_ms = min(slow_times) / number * 1000
    fast_ms = min(fast_times) / number * 1000
    speedup = slow_ms / fast_ms

    print(f"  Workload: {len(records)} records, 3 distinct schemas")
    print()
    print(f"  Uncached (load_schema per record):  {slow_ms:.1f}ms")
    print(f"  Cached   (lru_cache, warm):         {fast_ms:.2f}ms")
    print(f"  Speedup: {speedup:.0f}×")
    print()
    info = load_schema_cached.cache_info()
    print(f"  Cache info: {info}")


# ══════════════════════════════════════════════════════════════════════════════
# PART 5: lru_cache rules and limitations
#
# USE when:
#   - Function is PURE (same inputs → same outputs, no side effects)
#   - Input space is bounded (not one unique key per record)
#   - Function is called repeatedly with the same inputs in the same process
#
# DO NOT USE when:
#   - Function has side effects (writes to DB, sends email)
#   - Inputs are mutable (lists, dicts) — lru_cache requires hashable args
#   - Input space is unbounded (e.g., one unique user_id per call — cache fills
#     and evicts immediately, adding overhead with no benefit)
#   - Results change over time (file on disk is updated — stale cache)
# ══════════════════════════════════════════════════════════════════════════════

def demo_cache_rules():
    print("\n" + "=" * 60)
    print("PART 4: lru_cache rules and limitations")
    print("=" * 60)
    print()

    # maxsize=None → unbounded cache (cache grows to hold all unique keys)
    @lru_cache(maxsize=None)
    def expensive_compute(n: int) -> int:
        """Pure CPU computation — perfect candidate for caching."""
        return sum(i * i for i in range(n))

    # Demonstrate: bounded cache eviction
    @lru_cache(maxsize=3)
    def tiny_cache(key: str) -> str:
        return f"result_for_{key}"

    # Fill beyond maxsize
    for k in ["a", "b", "c", "d"]:
        tiny_cache(k)

    info = tiny_cache.cache_info()
    print(f"  tiny_cache maxsize=3, called with 4 keys:")
    print(f"    {info}")
    print(f"    currsize={info.currsize}  (oldest key evicted)")
    print()

    # Demonstrate: unhashable argument
    print("  Unhashable arguments raise TypeError:")
    try:
        @lru_cache(maxsize=32)
        def bad_cache(data: list) -> int:
            return len(data)
        bad_cache([1, 2, 3])
    except TypeError as e:
        print(f"    TypeError: {e}")
    print()

    # Demonstrate: unbounded input space — cache fills and evicts
    @lru_cache(maxsize=128)
    def per_user_lookup(user_id: int) -> str:
        return f"user_{user_id}"

    for i in range(200):   # 200 unique keys, cache evicts after 128
        per_user_lookup(i)
    info = per_user_lookup.cache_info()
    print(f"  per_user_lookup with 200 unique ids, maxsize=128:")
    print(f"    hits={info.hits}  misses={info.misses}  currsize={info.currsize}")
    print(f"    Hit rate: {info.hits/(info.hits+info.misses):.0%}")
    print(f"    → Poor fit for lru_cache: unbounded keys, few repeat lookups")


def main():
    demo_profile_uncached()
    demo_profile_cached()
    demo_benchmark()
    demo_cache_rules()


if __name__ == "__main__":
    main()

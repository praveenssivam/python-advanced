"""
05_generators_vs_lists.py
==========================
Memory and throughput tradeoffs between lists and generators.

Topics:
  1. Eager (list) vs lazy (generator) evaluation
  2. tracemalloc — measuring memory allocated by each approach
  3. Processing pipeline: generators chain without intermediate collections
  4. When generators are wrong (multiple passes, random access, len())

Run:
    python demo/module-07/05_generators_vs_lists.py
"""

import tracemalloc
import timeit
import sys


# ══════════════════════════════════════════════════════════════════════════════
# PART 1: List comprehension vs generator expression — memory side by side
#
# List comprehension:  builds the ENTIRE collection in memory
# Generator expression: yields one value at a time — O(1) memory
#
# For a collection of N items:
#   list:      O(N) memory, available immediately, supports indexing/len
#   generator: O(1) memory, one-pass only, no indexing, no len
# ══════════════════════════════════════════════════════════════════════════════

def make_records(n: int) -> list[dict]:
    return [{"id": i, "value": i * 2.5, "tag": f"tag_{i % 10}"} for i in range(n)]


def demo_memory_comparison():
    print("=" * 60)
    print("PART 1: Memory — list comprehension vs generator expression")
    print("=" * 60)
    print()

    N = 500_000
    data = list(range(N))

    # --- List comprehension ---
    tracemalloc.start()
    snapshot_before = tracemalloc.take_snapshot()

    result_list = [x * 2 for x in data]

    snapshot_after = tracemalloc.take_snapshot()
    stats = snapshot_after.compare_to(snapshot_before, "lineno")
    list_mem = sum(s.size_diff for s in stats if s.size_diff > 0)
    tracemalloc.stop()

    # --- Generator expression ---
    tracemalloc.start()
    snapshot_before = tracemalloc.take_snapshot()

    result_gen = (x * 2 for x in data)
    # Consume it to measure the sum (without building a list)
    total_gen = sum(result_gen)

    snapshot_after = tracemalloc.take_snapshot()
    stats = snapshot_after.compare_to(snapshot_before, "lineno")
    gen_mem = sum(s.size_diff for s in stats if s.size_diff > 0)
    tracemalloc.stop()

    total_list = sum(result_list)
    assert total_list == total_gen, "Results must match"

    # sys.getsizeof shows the object itself (not element storage for generators)
    list_obj_size = sys.getsizeof(result_list)
    gen_obj_size = sys.getsizeof((x * 2 for x in data))  # new gen for sizing

    print(f"  N = {N:,} integers")
    print()
    print(f"  List comprehension:")
    print(f"    sys.getsizeof(list):  {list_obj_size / 1024 / 1024:.2f} MB  (array of pointers)")
    print(f"    Allocated during build: ~{list_mem / 1024 / 1024:.1f} MB")
    print()
    print(f"  Generator expression:")
    print(f"    sys.getsizeof(gen):   {gen_obj_size} bytes  (single generator object!)")
    print(f"    Allocated during consume: ~{gen_mem / 1024:.0f} KB  (near zero extra)")
    print()
    print(f"  Result identical: sum={total_list:,}")
    print()
    print("  Key rule: if you only iterate ONCE and don't need indexing → generator.")


# ══════════════════════════════════════════════════════════════════════════════
# PART 2: Lazy pipeline — generators chain without intermediate collections
#
# Eager pipeline:   validated = [..list..]  → normalized = [..list..]  → exported = [..list..]
#                   3 full lists in memory simultaneously
#
# Lazy pipeline:    generators chain — each record flows through all stages
#                   one at a time.  Only one record in memory per stage.
# ══════════════════════════════════════════════════════════════════════════════

def validate(record: dict) -> dict | None:
    if record["value"] >= 0:
        return record
    return None


def normalize(record: dict) -> dict:
    return {**record, "tag": record["tag"].upper()}


def export(record: dict) -> str:
    return f"{record['id']}:{record['value']:.1f}:{record['tag']}"


# --- Eager: three full lists ---
def process_eager(records: list[dict]) -> list[str]:
    validated  = [r for r in records if validate(r) is not None]    # list 1
    normalized = [normalize(r) for r in validated]                  # list 2
    exported   = [export(r)    for r in normalized]                 # list 3
    return exported


# --- Lazy: three chained generators ---
def process_lazy(records: list[dict]):
    validated  = (r            for r in records    if validate(r) is not None)
    normalized = (normalize(r) for r in validated)
    exported   = (export(r)    for r in normalized)
    return exported   # returns a generator — single pass


def measure_memory(fn, *args) -> tuple[int, object]:
    """Returns (bytes_allocated, result)."""
    tracemalloc.start()
    before = tracemalloc.take_snapshot()
    result = fn(*args)
    # For generators, consume to trigger execution
    if hasattr(result, "__next__"):
        result = list(result)
    after = tracemalloc.take_snapshot()
    diff = sum(s.size_diff for s in after.compare_to(before, "lineno")
               if s.size_diff > 0)
    tracemalloc.stop()
    return diff, result


def demo_pipeline():
    print("\n" + "=" * 60)
    print("PART 2: Lazy pipeline — generators chain without temp collections")
    print("=" * 60)
    print()

    N = 100_000
    records = make_records(N)

    eager_bytes, eager_result = measure_memory(process_eager, records)
    lazy_bytes, lazy_result   = measure_memory(process_lazy, records)

    assert eager_result == lazy_result, "Pipeline results must match"

    print(f"  Pipeline: validate → normalize → export   ({N:,} records)")
    print()
    print(f"  Eager (3 intermediate lists):  {eager_bytes / 1024 / 1024:.1f} MB allocated")
    print(f"  Lazy  (3 chained generators):  {lazy_bytes  / 1024 / 1024:.2f} MB allocated")
    print(f"  Memory reduction: {eager_bytes / max(lazy_bytes, 1):.0f}×")
    print()
    print("  Lazy pipeline holds at most ONE record per stage in memory.")
    print("  Scales to arbitrarily large datasets without increasing RAM.")


# ══════════════════════════════════════════════════════════════════════════════
# PART 3: Speed — when lists ARE faster
#
# Generators save memory but add per-yield overhead.  For small N or when
# the consumer needs random access, lists can be faster.
#
# Rule:
#   - Memory is the constraint (large N, streaming) → generator
#   - Multi-pass, indexing, len() required          → list
#   - Hot inner loop on small data                  → list (lower overhead)
# ══════════════════════════════════════════════════════════════════════════════

def demo_speed_tradeoff():
    print("\n" + "=" * 60)
    print("PART 3: Speed tradeoff — when lists are faster")
    print("=" * 60)
    print()

    data = list(range(1000))
    number = 10_000

    # Small N — generator overhead per-yield vs list tight iteration
    list_time = timeit.timeit(
        lambda: sum([x * 2 for x in data]),
        number=number
    )
    gen_time = timeit.timeit(
        lambda: sum(x * 2 for x in data),
        number=number
    )

    list_us = list_time / number * 1_000_000
    gen_us  = gen_time  / number * 1_000_000

    print(f"  sum() over N={len(data)} — {number:,} runs")
    print(f"    list comprehension: {list_us:.1f}µs")
    print(f"    generator expr:     {gen_us:.1f}µs")
    print()
    if list_us < gen_us:
        print(f"  List is {gen_us/list_us:.1f}× faster for small N — generator overhead dominates.")
    else:
        print(f"  Generator is {list_us/gen_us:.1f}× faster — likely due to GC savings.")
    print()
    print("  For large N (memory pressure), generator wins on RAM even if")
    print("  slightly slower in CPU time — the GC pauses from large lists")
    print("  dominate total wall-clock time.")


# ══════════════════════════════════════════════════════════════════════════════
# PART 4: Generator anti-patterns
#
# 1. Iterating a generator twice — second pass yields nothing
# 2. Using len() on a generator — raises TypeError
# 3. Random access (gen[i]) — raises TypeError
# ══════════════════════════════════════════════════════════════════════════════

def demo_generator_gotchas():
    print("\n" + "=" * 60)
    print("PART 4: Generator anti-patterns — what NOT to do")
    print("=" * 60)
    print()

    # Anti-pattern 1: iterate twice
    numbers = (x for x in range(5))
    first_pass  = list(numbers)
    second_pass = list(numbers)   # exhausted — yields nothing
    print(f"  GOTCHA 1: iterate twice")
    print(f"    first pass:  {first_pass}")
    print(f"    second pass: {second_pass}  ← empty! generator is exhausted")
    print()

    # Anti-pattern 2: len() on generator
    gen = (x for x in range(5))
    print(f"  GOTCHA 2: len() raises TypeError")
    try:
        print(len(gen))
    except TypeError as e:
        print(f"    TypeError: {e}")
    print()

    # Anti-pattern 3: indexing
    gen = (x for x in range(5))
    print(f"  GOTCHA 3: indexing raises TypeError")
    try:
        print(gen[0])
    except TypeError as e:
        print(f"    TypeError: {e}")
    print()

    print("  Fix for all three: if you need multi-pass / len / index → use list()")
    print("    results = list(process_lazy(records))  # materialise once, reuse")


def main():
    demo_memory_comparison()
    demo_pipeline()
    demo_speed_tradeoff()
    demo_generator_gotchas()


if __name__ == "__main__":
    main()

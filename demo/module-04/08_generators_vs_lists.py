"""
08_generators_vs_lists.py
==========================
A generator is an object that produces values ON DEMAND, one at a time,
rather than computing all values up front and storing them in memory.

  List comprehension:      [f(x) for x in items]   ← all items in memory NOW
  Generator expression:    (f(x) for x in items)   ← nothing computed yet

The generator computes each item only when you call next() or iterate over it.

When to prefer generators:
  • Large or infinite sequences (avoid memory overhead)
  • Early-exit pipelines (stop when you find what you need)
  • Chained transformations (each stage is lazy)

Run:
    python demo/module-04/08_generators_vs_lists.py
"""

import sys
from typing import Generator, Iterable


# ══════════════════════════════════════════════════════════════════════════════
# PART 1: Memory comparison — list vs generator
#
# list comprehension: allocates a list and FILLS it entirely before returning.
# generator expression: returns a generator object immediately (size ~120 bytes)
#   — no values computed yet; iteration triggers computation one-by-one.
#
# For 1 million floats:
#   list ≈ 8 MB
#   generator ≈ 120 bytes   (just the generator object, no stored values)
# ══════════════════════════════════════════════════════════════════════════════

def demo_memory_comparison():
    print("=" * 55)
    print("PART 1: Memory — list vs generator")
    print("=" * 55)
    print()

    n = 1_000_000

    list_result      = [x * 0.01 for x in range(n)]
    generator_result = (x * 0.01 for x in range(n))

    list_size = sys.getsizeof(list_result)
    gen_size  = sys.getsizeof(generator_result)

    print(f"  n = {n:,}")
    print(f"  List comprehension size:  {list_size:>10,} bytes  ({list_size // 1024:,} KB)")
    print(f"  Generator expression size:{gen_size:>10,} bytes  (just the object; "
          f"values not computed yet)")
    print()
    print("  Generator ratio: list is "
          f"~{list_size // gen_size:,}x larger than generator in memory.")


# ══════════════════════════════════════════════════════════════════════════════
# PART 2: Lazy evaluation — step-by-step via next()
#
# Flow for gen = squares(n):
#   • squares(n) is called → immediately returns a generator object
#   • NO computation happens yet
#   • next(gen) → runs up to the first 'yield'; yields the value; pauses
#   • next(gen) → resumes from after the yield; runs to next yield; pauses
#   • StopIteration raised when the function body completes
# ══════════════════════════════════════════════════════════════════════════════

def squares(n: int) -> Generator[int, None, None]:
    """Generate n*n values for n = 0, 1, 2, ..., up-to-N."""
    print(f"  [squares] generator created — nothing computed yet")
    for i in range(n):
        print(f"  [squares] about to yield {i}² = {i*i}")
        yield i * i
        print(f"  [squares] resumed after yielding {i}²")
    print(f"  [squares] generator exhausted")


def demo_lazy_evaluation():
    print("\n" + "=" * 55)
    print("PART 2: Lazy evaluation — step-by-step")
    print("=" * 55)
    print()

    gen = squares(3)
    print(f"  gen = squares(3) → generator object: {gen}")
    print(f"  (Notice: '[squares] generator created' printed above, but no yields yet!)")
    print()

    print("  next(gen):")
    val = next(gen)
    print(f"  → got {val}")
    print()

    print("  next(gen):")
    val = next(gen)
    print(f"  → got {val}")
    print()

    print("  next(gen):")
    val = next(gen)
    print(f"  → got {val}")
    print()

    print("  next(gen):")
    try:
        next(gen)
    except StopIteration:
        print("  → StopIteration raised  (generator exhausted)")


# ══════════════════════════════════════════════════════════════════════════════
# PART 3: Chaining generators — lazy pipeline
#
# Each generator reads from the previous one — data flows through the chain
# one item at a time.  None of the stages buffer anything.
#
# Pipeline:
#   read_rows  → yields raw rows from a list (simulates file reading)
#   parse_fare → yields float fares, skipping unparseable rows
#   filter_pos → yields only positive fares
#
# Flow for consume(pipeline):
#   for item in pipeline:           ← pulls from filter_pos
#     filter_pos pulls from parse_fare
#     parse_fare pulls from read_rows
#     Only one row lives in memory at any time
# ══════════════════════════════════════════════════════════════════════════════

def read_rows(data: list) -> Generator:
    """Simulates reading rows from a large file."""
    for row in data:
        yield row


def parse_fare(rows: Iterable) -> Generator[float, None, None]:
    """Parse each row's 'fare' field as float; skip malformed rows."""
    for row in rows:
        try:
            yield float(row["fare"])
        except (ValueError, KeyError):
            pass   # silently skip bad data


def filter_positive(fares: Iterable[float]) -> Generator[float, None, None]:
    """Keep only fares greater than zero."""
    for fare in fares:
        if fare > 0:
            yield fare


def demo_generator_pipeline():
    print("\n" + "=" * 55)
    print("PART 3: Chained generator pipeline")
    print("=" * 55)
    print()

    raw_data = [
        {"trip_id": "T1", "fare": "12.50"},
        {"trip_id": "T2", "fare": "0"},          # zero → filtered out
        {"trip_id": "T3", "fare": "bad_data"},    # parse error → skipped
        {"trip_id": "T4", "fare": "-5.00"},       # negative → filtered out
        {"trip_id": "T5", "fare": "8.75"},
        {"trip_id": "T6", "fare": "22.00"},
    ]

    # Build the pipeline — nothing executes yet
    pipeline = filter_positive(parse_fare(read_rows(raw_data)))

    print("  Pipeline built — no computation yet.")
    print("  Consuming:")
    fares = list(pipeline)   # pulling all results
    print(f"  Collected fares: {fares}")
    print(f"  Total: {sum(fares):.2f}")


# ══════════════════════════════════════════════════════════════════════════════
# PART 4: Early exit — generator stops as soon as you stop consuming
#
# With a list, the full computation always runs.
# With a generator, processing halts the moment iteration stops.
# ══════════════════════════════════════════════════════════════════════════════

def generate_with_log(items: list) -> Generator:
    """Yields items one at a time, printing when each is produced."""
    for item in items:
        print(f"  [generator] producing: {item}")
        yield item


def demo_early_exit():
    print("\n" + "=" * 55)
    print("PART 4: Early exit — stop consuming, stop computing")
    print("=" * 55)
    print()

    items = ["A", "B", "C", "D", "E"]

    print("  list comprehension — ALL items computed before access:")
    listcomp = [x.lower() for x in items]   # all 5 computed now
    first = listcomp[0]
    print(f"  first = {first!r}  (rest of list still in memory)\n")

    print("  generator — only items you consume are computed:")
    gen = generate_with_log(items)
    first = next(gen)
    print(f"  first = {first!r}  (B, C, D, E never computed)\n")

    print("  ...continuing iteration to show all remaining items:")
    for item in gen:
        pass   # consume rest so the demo is tidy


def main():
    demo_memory_comparison()
    demo_lazy_evaluation()
    demo_generator_pipeline()
    demo_early_exit()


if __name__ == "__main__":
    main()

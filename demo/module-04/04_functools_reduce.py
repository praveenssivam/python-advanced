"""
04_functools_reduce.py
========================
functools.reduce(fn, iterable[, initial]) applies a two-argument
function cumulatively to items in the iterable, reducing it to a
single value.

reduce(fn, [a, b, c, d])
  → fn(fn(fn(a, b), c), d)

This is the functional equivalent of a for-loop accumulator.

Run:
    python demo/module-04/04_functools_reduce.py
"""

from functools import reduce
import operator


# ══════════════════════════════════════════════════════════════════════════════
# PART 1: Mechanics — reduce visualised step by step
#
# reduce(fn, items) begins with item[0] as the accumulator.
# At each step: accumulator = fn(accumulator, next_item)
#
# reduce(fn, items, initial) uses 'initial' as the starting accumulator.
# Use this when the iterable may be empty.
#
# reduce(add, [1, 2, 3, 4]):
#   step 1: acc = add(1, 2) → 3
#   step 2: acc = add(3, 3) → 6
#   step 3: acc = add(6, 4) → 10
# ══════════════════════════════════════════════════════════════════════════════

def traced_reduce(fn, items, initial=None):
    """Run reduce and print each accumulation step for teaching purposes."""
    items = list(items)
    if initial is not None:
        acc = initial
        print(f"  initial = {initial!r}")
    else:
        acc = items[0]
        items = items[1:]
        print(f"  start   = {acc!r}")

    for item in items:
        new_acc = fn(acc, item)
        print(f"  fn({acc!r}, {item!r}) → {new_acc!r}")
        acc = new_acc
    return acc


def demo_mechanics():
    print("=" * 55)
    print("PART 1: How reduce works — step-by-step trace")
    print("=" * 55)
    print()

    numbers = [1, 2, 3, 4, 5]

    print("reduce(add, [1,2,3,4,5]):")
    result = traced_reduce(operator.add, numbers)
    print(f"  result = {result}")

    print()
    print("reduce(multiply, [1,2,3,4,5]):")
    result = traced_reduce(operator.mul, numbers)
    print(f"  result = {result}")

    print()
    print("reduce(add, [1,2,3], initial=100):")
    result = traced_reduce(operator.add, [1, 2, 3], initial=100)
    print(f"  result = {result}")


# ══════════════════════════════════════════════════════════════════════════════
# PART 2: Practical uses
#
# - Sum / product of a list of numbers
# - Flatten a list of lists
# - Build a dict by merging many dicts
# - Find the maximum manually (to understand the pattern)
#
# Note: for sum and max, Python's built-in sum()/max() are clearer —
# the educational value here is understanding the accumulator pattern.
# ══════════════════════════════════════════════════════════════════════════════

def demo_practical_uses():
    print("\n" + "=" * 55)
    print("PART 2: Practical uses")
    print("=" * 55)
    print()

    # ── Flatten a list of lists ───────────────────────────────────────────────
    # Flow: reduce(concat_lists, [[1,2],[3,4],[5]])
    #   step 1: acc = [1,2] + [3,4] → [1,2,3,4]
    #   step 2: acc = [1,2,3,4] + [5] → [1,2,3,4,5]
    nested = [[1, 2], [3, 4], [5, 6], [7]]
    flattened = reduce(lambda acc, lst: acc + lst, nested)
    print(f"Flatten {nested}:")
    print(f"  reduce(concat, nested) = {flattened}")

    print()
    # ── Merge dicts (later dicts win on key conflict) ─────────────────────────
    # Flow: reduce(merge, [d1, d2, d3])
    #   step 1: {**d1, **d2} → merged
    #   step 2: {**merged, **d3} → final
    dicts = [
        {"source": "s3", "region": "ap-south-1"},
        {"format": "parquet", "region": "us-east-1"},  # overrides region
        {"parallelism": 4},
    ]
    merged = reduce(lambda acc, d: {**acc, **d}, dicts)
    print(f"Merge dicts (later wins on conflict):")
    for d in dicts:
        print(f"  + {d}")
    print(f"  → {merged}")

    print()
    # ── Manual maximum ────────────────────────────────────────────────────────
    # Flow: reduce(max_fn, [3,1,4,1,5,9,2,6])
    #   keeps the running maximum at each step
    values = [3, 1, 4, 1, 5, 9, 2, 6]
    manual_max = reduce(lambda a, b: a if a > b else b, values)
    print(f"Manual max via reduce on {values}:")
    print(f"  = {manual_max}  (same as max({values}) = {max(values)})")

    print()
    # ── Compute total pipeline duration from steps ────────────────────────────
    steps = [
        {"name": "extract",   "duration_s": 12},
        {"name": "validate",  "duration_s": 3},
        {"name": "transform", "duration_s": 7},
        {"name": "load",      "duration_s": 5},
    ]
    total_s = reduce(lambda acc, step: acc + step["duration_s"], steps, 0)
    print(f"Total pipeline duration from steps:")
    for s in steps:
        print(f"  + {s['name']}: {s['duration_s']}s")
    print(f"  = {total_s}s total")


# ══════════════════════════════════════════════════════════════════════════════
# PART 3: reduce vs. for-loop — when each is clearer
#
# reduce is expressive for well-understood accumulations (sum, product, merge).
# A for-loop is clearer when the accumulation logic is complex or multi-step.
# ══════════════════════════════════════════════════════════════════════════════

def demo_reduce_vs_loop():
    print("\n" + "=" * 55)
    print("PART 3: reduce vs. explicit for-loop")
    print("=" * 55)
    print()

    sales = [120.0, 340.5, 88.0, 400.0, 55.5]

    # reduce version
    total_reduce = reduce(operator.add, sales)

    # for-loop version — equivalent, more readable for beginners
    total_loop = 0.0
    for s in sales:
        total_loop += s

    print(f"reduce(add, sales)   = {total_reduce}")
    print(f"for-loop sum         = {total_loop}")
    print(f"sum(sales)           = {sum(sales)}")
    print()
    print("All three give the same result.")
    print("Rule of thumb:")
    print("  - Use sum(), max(), min() for standard aggregations (clearest).")
    print("  - Use reduce() for custom binary accumulation (merge, flatten, etc.).")
    print("  - Use a for-loop when the accumulation logic is multi-step.")


def main():
    demo_mechanics()
    demo_practical_uses()
    demo_reduce_vs_loop()


if __name__ == "__main__":
    main()

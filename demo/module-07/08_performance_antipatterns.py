"""
08_performance_antipatterns.py
================================
Five performance anti-patterns with measurements showing the cost.

Topics:
  1. Optimizing before measuring — wasted effort on a function that isn't slow
  2. String concatenation in a loop (quadratic allocation)
  3. Repeated attribute/method lookup in a tight loop
  4. List.remove() in a loop — O(n²) scan
  5. Using exceptions for control flow in a hot path

Run:
    python demo/module-07/08_performance_antipatterns.py
"""

import timeit
import cProfile
import pstats
import io


# ══════════════════════════════════════════════════════════════════════════════
# ANTI-PATTERN 1: Optimizing before measuring
#
# This is the most expensive anti-pattern — it costs engineering time.
# Demonstrated by showing TWO functions: one that looks slow, one that is slow.
# The "obvious" bottleneck is not the real one.
# ══════════════════════════════════════════════════════════════════════════════

def looks_slow(n: int) -> int:
    """Has a nested loop — looks O(n²), but inner loop is tiny."""
    total = 0
    for i in range(n):
        for j in range(5):   # inner loop is constant size 5 — O(5n) = O(n)
            total += i * j
    return total


def actually_slow(items: list[str]) -> list[str]:
    """Innocent-looking string join — hides O(n²) allocation."""
    result = ""
    for item in items:
        result += item + ","   # creates a new string object on every iteration
    return result.split(",")


def demo_measure_first():
    print("=" * 60)
    print("ANTI-PATTERN 1: Optimizing before measuring")
    print("=" * 60)
    print()
    print("  Two functions — which one should you optimize first?")
    print()

    N = 5_000
    items = [f"item_{i}" for i in range(N)]
    number = 200

    t_looks = min(timeit.repeat(lambda: looks_slow(N), number=number, repeat=3)) / number * 1_000_000
    t_actual = min(timeit.repeat(lambda: actually_slow(items), number=30, repeat=3)) / 30 * 1000

    print(f"  looks_slow({N}):          {t_looks:.0f}µs   ← nested loop, looks scary")
    print(f"  actually_slow({N} items): {t_actual:.1f}ms  ← innocent one-liner")
    print()
    print(f"  Ratio: actually_slow is {t_actual*1000/t_looks:.0f}× SLOWER than looks_slow!")
    print()
    print("  Moral: the nested loop has a constant inner size (5).")
    print("  The one-liner has quadratic string allocation — profile first!")
    print()
    print("  Profile output (run on actually_slow):")

    profiler = cProfile.Profile()
    profiler.enable()
    actually_slow(items)
    profiler.disable()
    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.strip_dirs()
    stats.sort_stats("tottime")
    stats.print_stats(5)
    for line in stream.getvalue().splitlines()[6:12]:
        if line.strip():
            print(f"    {line}")


# ══════════════════════════════════════════════════════════════════════════════
# ANTI-PATTERN 2: String concatenation in a loop
#
# str += str is O(n) per concatenation because it creates a new string object.
# Over n iterations: O(1) + O(2) + ... + O(n) = O(n²) total.
#
# Fix: collect into a list, join at the end — O(n) total.
# ══════════════════════════════════════════════════════════════════════════════

def build_csv_concat(rows: list[list]) -> str:
    """BAD: += creates a new string on every row — O(n²) allocations."""
    result = ""
    for row in rows:
        result += ",".join(str(v) for v in row) + "\n"
    return result


def build_csv_join(rows: list[list]) -> str:
    """GOOD: collect into list, join once — O(n) total allocations."""
    parts = []
    for row in rows:
        parts.append(",".join(str(v) for v in row))
    return "\n".join(parts) + "\n"


def build_csv_genexpr(rows: list[list]) -> str:
    """BEST: single join over a generator — no intermediate list."""
    return "\n".join(",".join(str(v) for v in row) for row in rows) + "\n"


def demo_string_concat():
    print("\n" + "=" * 60)
    print("ANTI-PATTERN 2: String concatenation in a loop")
    print("=" * 60)
    print()

    rows = [[i, i * 2, f"tag_{i}", i * 1.5] for i in range(2_000)]
    number = 100

    t_concat = min(timeit.repeat(lambda: build_csv_concat(rows), number=number, repeat=3)) / number * 1000
    t_join   = min(timeit.repeat(lambda: build_csv_join(rows),   number=number, repeat=3)) / number * 1000
    t_gen    = min(timeit.repeat(lambda: build_csv_genexpr(rows), number=number, repeat=3)) / number * 1000

    # Verify outputs match
    assert build_csv_concat(rows) == build_csv_join(rows) == build_csv_genexpr(rows)

    print(f"  Building CSV for {len(rows):,} rows")
    print()
    print(f"  BAD  (result += line):          {t_concat:.3f}ms")
    print(f"  GOOD (parts.append + join):     {t_join:.3f}ms   ({t_concat/t_join:.1f}× faster)")
    print(f"  BEST (single join genexpr):     {t_gen:.3f}ms   ({t_concat/t_gen:.1f}× faster)")
    print()
    print("  Rule: NEVER concatenate strings in a hot loop.")
    print("  Always collect to a list, then ''.join(parts).")


# ══════════════════════════════════════════════════════════════════════════════
# ANTI-PATTERN 3: Repeated attribute lookup in a tight loop
#
# obj.method() in a Python loop performs a dict lookup in obj.__dict__
# on every iteration.  For a function called millions of times, this adds up.
#
# Fix: bind the method to a local name before the loop.
# ══════════════════════════════════════════════════════════════════════════════

def count_words_attr_lookup(text: str) -> int:
    """BAD: list.append looked up via attribute on every iteration."""
    words = text.split()
    result = []
    for w in words:
        result.append(w.lower())   # result.append looked up each time
    return len(result)


def count_words_local_bind(text: str) -> int:
    """GOOD: bind append to a local variable — avoids attribute lookup."""
    words = text.split()
    result = []
    append = result.append   # LOCAL BIND — one lookup before loop
    for w in words:
        append(w.lower())
    return len(result)


def demo_attribute_lookup():
    print("\n" + "=" * 60)
    print("ANTI-PATTERN 3: Repeated attribute lookup in a tight loop")
    print("=" * 60)
    print()

    text = "the quick brown fox jumps over the lazy dog " * 5_000
    number = 500

    t_attr  = min(timeit.repeat(lambda: count_words_attr_lookup(text), number=number, repeat=3)) / number * 1000
    t_local = min(timeit.repeat(lambda: count_words_local_bind(text),  number=number, repeat=3)) / number * 1000

    assert count_words_attr_lookup(text) == count_words_local_bind(text)

    print(f"  {len(text.split()):,} words, {number} iterations")
    print()
    print(f"  BAD  (result.append in loop):   {t_attr:.3f}ms")
    print(f"  GOOD (local bind before loop):  {t_local:.3f}ms   ({t_attr/t_local:.1f}× faster)")
    print()
    print("  Note: list comprehension is even better — it avoids the append call entirely.")
    t_lc = min(timeit.repeat(
        lambda: [w.lower() for w in text.split()], number=number, repeat=3
    )) / number * 1000
    print(f"  BEST (list comprehension):      {t_lc:.3f}ms   ({t_attr/t_lc:.1f}× faster)")


# ══════════════════════════════════════════════════════════════════════════════
# ANTI-PATTERN 4: list.remove() in a loop — O(n²)
#
# list.remove(x) does a linear scan to find x and then shifts all elements
# after it: O(n) per call.  Calling it N times = O(n²).
#
# Fix: use a set for O(1) removal, or build a new list with a comprehension.
# ══════════════════════════════════════════════════════════════════════════════

def remove_banned_bad(items: list[str], banned: set[str]) -> list[str]:
    """BAD: list.remove() is O(n) per call — total O(n²)."""
    result = list(items)
    for b in banned:
        while b in result:
            result.remove(b)   # O(n) scan + shift on each call
    return result


def remove_banned_good(items: list[str], banned: set[str]) -> list[str]:
    """GOOD: list comprehension — O(n) total."""
    return [item for item in items if item not in banned]


def demo_list_remove():
    print("\n" + "=" * 60)
    print("ANTI-PATTERN 4: list.remove() in a loop — O(n²)")
    print("=" * 60)
    print()

    N = 5_000
    items  = [f"item_{i}" for i in range(N)]
    banned = {f"item_{i}" for i in range(0, N, 10)}   # every 10th item — 500 banned

    # Add some items to input that need removing
    mixed = items + list(banned)

    t_bad  = min(timeit.repeat(lambda: remove_banned_bad(mixed, banned),  number=20, repeat=3)) / 20 * 1000
    t_good = min(timeit.repeat(lambda: remove_banned_good(mixed, banned), number=200, repeat=3)) / 200 * 1000

    assert sorted(remove_banned_bad(mixed, banned)) == sorted(remove_banned_good(mixed, banned))

    print(f"  {len(mixed):,} items, {len(banned):,} banned values")
    print()
    print(f"  BAD  (list.remove() per banned):   {t_bad:.2f}ms")
    print(f"  GOOD (list comprehension):         {t_good:.3f}ms   ({t_bad/t_good:.0f}× faster)")
    print()
    print("  Rule: list.remove() is O(n). Never call it inside a loop over large data.")
    print("  Use set membership (O(1)) or a comprehension filter instead.")


# ══════════════════════════════════════════════════════════════════════════════
# ANTI-PATTERN 5: Exceptions for control flow in a hot path
#
# raise/except is expensive in Python — it builds a full traceback.
# Using try/except for expected control flow (e.g., checking if a key
# exists in a dict) is much slower than an explicit check.
#
# Rule: exceptions should be EXCEPTIONAL.  Use if/else for expected cases.
# ══════════════════════════════════════════════════════════════════════════════

def get_value_exception(data: dict, key: str) -> int:
    """BAD: uses exception to handle missing key — expensive when key is often absent."""
    try:
        return data[key]
    except KeyError:
        return 0


def get_value_conditional(data: dict, key: str) -> int:
    """GOOD: dict.get() with default — O(1) hash lookup, no exception overhead."""
    return data.get(key, 0)


def demo_exception_control_flow():
    print("\n" + "=" * 60)
    print("ANTI-PATTERN 5: Exceptions for control flow")
    print("=" * 60)
    print()

    data = {f"key_{i}": i for i in range(1_000)}
    # Mix of hits and misses — 50% missing
    keys = [f"key_{i}" for i in range(2_000)]
    number = 2_000

    t_exc   = min(timeit.repeat(lambda: [get_value_exception(data, k)    for k in keys], number=number, repeat=3)) / number * 1000
    t_cond  = min(timeit.repeat(lambda: [get_value_conditional(data, k)  for k in keys], number=number, repeat=3)) / number * 1000

    assert [get_value_exception(data, k) for k in keys] == [get_value_conditional(data, k) for k in keys]

    print(f"  {len(keys):,} key lookups (50% missing)")
    print()
    print(f"  BAD  (try/except KeyError):   {t_exc:.3f}ms")
    print(f"  GOOD (dict.get(key, 0)):      {t_cond:.3f}ms   ({t_exc/t_cond:.1f}× faster)")
    print()
    print("  Exception overhead comes from building the traceback frame.")
    print("  When exceptions are EXPECTED (50% miss rate), the cost compounds.")
    print()
    print("  Legitimate use of exceptions: truly unexpected errors,")
    print("  not expected control flow (missing key, invalid type check).")


def main():
    demo_measure_first()
    demo_string_concat()
    demo_attribute_lookup()
    demo_list_remove()
    demo_exception_control_flow()


if __name__ == "__main__":
    main()

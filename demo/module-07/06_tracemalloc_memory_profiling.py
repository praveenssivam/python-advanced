"""
06_tracemalloc_memory_profiling.py
====================================
Finding memory hotspots with tracemalloc.

Topics:
  1. tracemalloc.start() / take_snapshot() / statistics()
  2. Top allocation sites — file:lineno with sizes
  3. Comparing two snapshots (before/after)
  4. tracemalloc.get_traced_memory() — peak usage

Run:
    python demo/module-07/06_tracemalloc_memory_profiling.py
"""

import tracemalloc
import re
import sys


# ══════════════════════════════════════════════════════════════════════════════
# PART 1: tracemalloc basics
#
# tracemalloc hooks Python's memory allocator and records WHERE each
# allocation was made (file + line number).
#
# Workflow:
#   tracemalloc.start()           ← start recording allocations
#   ... run your code ...
#   snapshot = take_snapshot()    ← freeze the allocation map
#   stats = snapshot.statistics("lineno")  ← group by file:lineno
#   for stat in stats[:10]: print(stat)
#
# Output for each allocation site:
#   filename:lineno: size=N KiB, count=M, average=A B
# ══════════════════════════════════════════════════════════════════════════════

def build_report(n: int) -> dict:
    """
    Simulates building a validation report with several allocation patterns:
    - A list of records (one object per record)
    - A dict of intermediate results
    - Compiled per-record string messages
    """
    records   = [{"id": i, "email": f"u{i}@x.com", "value": i * 1.5} for i in range(n)]
    results   = {r["id"]: r["email"] + " OK" for r in records}   # dict + string allocs
    messages  = [f"Record {r['id']}: value={r['value']:.2f}" for r in records]
    return {"records": records, "results": results, "messages": messages}


def demo_basics():
    print("=" * 60)
    print("PART 1: tracemalloc — top allocation sites")
    print("=" * 60)
    print()

    tracemalloc.start()

    report = build_report(5_000)

    snapshot = tracemalloc.take_snapshot()
    tracemalloc.stop()

    # Filter to lines in THIS file only (exclude stdlib internals)
    this_file = __file__
    stats = snapshot.statistics("lineno")

    print(f"  Top allocation sites (all locations):")
    print(f"  {'Size':>10}  {'Count':>7}  Location")
    print(f"  {'─'*10}  {'─'*7}  {'─'*50}")
    for stat in stats[:10]:
        size_kb = stat.size / 1024
        print(f"  {size_kb:>9.1f}K  {stat.count:>7,}  {stat.traceback[0]}")

    print()
    total_kb = sum(s.size for s in stats) / 1024
    print(f"  Total tracked: {total_kb:.0f} KB")
    print()
    print("  Reading the output:")
    print("    size    = total bytes allocated at this site (still live)")
    print("    count   = number of live allocations from this line")
    print("    average = size / count (per object cost)")


# ══════════════════════════════════════════════════════════════════════════════
# PART 2: Comparing two snapshots — before vs after a change
#
# snapshot.compare_to(other, "lineno") returns a list of StatisticDiff objects.
# Each StatisticDiff has:
#   size_diff  — bytes allocated (positive = grew, negative = freed)
#   count_diff — allocation count change
#
# Use this to answer: "Where did the extra 50MB come from after my change?"
# ══════════════════════════════════════════════════════════════════════════════

def allocate_eager(data: list) -> list:
    """Builds an intermediate list — allocates ~N × object size."""
    return [str(x) + "_processed" for x in data]


def allocate_lazy(data: list):
    """Generator — allocates one string at a time."""
    return (str(x) + "_processed" for x in data)


def demo_snapshot_comparison():
    print("\n" + "=" * 60)
    print("PART 2: Comparing snapshots — before vs after")
    print("=" * 60)
    print()

    N = 100_000
    data = list(range(N))

    # --- Eager ---
    tracemalloc.start()
    snap1 = tracemalloc.take_snapshot()

    result_list = allocate_eager(data)   # full list in memory

    snap2 = tracemalloc.take_snapshot()
    tracemalloc.stop()

    diffs = snap2.compare_to(snap1, "lineno")
    eager_growth = sum(d.size_diff for d in diffs if d.size_diff > 0)

    # --- Lazy ---
    tracemalloc.start()
    snap3 = tracemalloc.take_snapshot()

    result_gen = allocate_lazy(data)     # generator — no allocation yet
    total = sum(len(x) for x in result_gen)  # consume, but no list stored

    snap4 = tracemalloc.take_snapshot()
    tracemalloc.stop()

    diffs_lazy = snap4.compare_to(snap3, "lineno")
    lazy_growth = sum(d.size_diff for d in diffs_lazy if d.size_diff > 0)

    print(f"  N = {N:,} strings")
    print()
    print(f"  allocate_eager  → snapshot growth: {eager_growth / 1024 / 1024:.2f} MB")
    print(f"  allocate_lazy   → snapshot growth: {lazy_growth  / 1024:.0f} KB")
    print(f"  Reduction: {eager_growth / max(lazy_growth, 1):.0f}×")
    print()
    print("  Top growth lines (eager):")
    for d in sorted(diffs, key=lambda x: -x.size_diff)[:3]:
        if d.size_diff > 0:
            print(f"    +{d.size_diff/1024:.0f}KB  {d.traceback[0]}")


# ══════════════════════════════════════════════════════════════════════════════
# PART 3: get_traced_memory() — current and peak usage
#
# tracemalloc.get_traced_memory() returns (current_bytes, peak_bytes)
# peak is the maximum live allocations since tracemalloc.start()
#
# Useful for confirming that a function's peak memory stays within budget.
# ══════════════════════════════════════════════════════════════════════════════

def demo_peak_memory():
    print("\n" + "=" * 60)
    print("PART 3: get_traced_memory() — current and peak usage")
    print("=" * 60)
    print()

    def memory_intensive(n: int) -> int:
        # Build a large list, then delete it — current drops but peak stays
        big = [i * i for i in range(n)]
        peak_inside = tracemalloc.get_traced_memory()[1]
        total = sum(big)
        del big   # list freed — current drops
        return total

    tracemalloc.start()
    cur_start, peak_start = tracemalloc.get_traced_memory()

    N = 200_000
    result = memory_intensive(N)

    cur_end, peak_end = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"  memory_intensive({N:,}) — sum of squares")
    print()
    print(f"  Before call:   current={cur_start:,} bytes    peak={peak_start:,} bytes")
    print(f"  After call:    current={cur_end:,} bytes")
    print(f"  Peak during:   {peak_end / 1024 / 1024:.2f} MB  ← list was in memory here")
    print()
    print("  'current' dropped after del — list freed.")
    print("  'peak' records the high-water mark — catches transient spikes.")
    print()
    print("  Rule: if peak >> current, you have a temporary allocation spike.")
    print("  Fix with generators or streaming to reduce transient peak.")


# ══════════════════════════════════════════════════════════════════════════════
# PART 4: Practical memory optimization table
# ══════════════════════════════════════════════════════════════════════════════

def demo_optimization_table():
    print("\n" + "=" * 60)
    print("PART 4: Memory optimization patterns")
    print("=" * 60)
    print()

    # __slots__ vs regular class memory comparison
    class RegularRecord:
        def __init__(self, id: int, email: str, value: float):
            self.id    = id
            self.email = email
            self.value = value

    class SlottedRecord:
        __slots__ = ("id", "email", "value")
        def __init__(self, id: int, email: str, value: float):
            self.id    = id
            self.email = email
            self.value = value

    regular = RegularRecord(1, "u@x.com", 1.5)
    slotted = SlottedRecord(1, "u@x.com", 1.5)

    regular_size = sys.getsizeof(regular) + sys.getsizeof(regular.__dict__)
    slotted_size = sys.getsizeof(slotted)

    print(f"  __slots__ memory saving per object:")
    print(f"    Regular class (with __dict__): {regular_size} bytes")
    print(f"    __slots__ class:               {slotted_size} bytes")
    print(f"    Saving per instance:           {regular_size - slotted_size} bytes")
    print()
    N_instances = 1_000_000
    saved_mb = (regular_size - slotted_size) * N_instances / 1024 / 1024
    print(f"    At {N_instances:,} instances: saves {saved_mb:.0f} MB")
    print()
    print("  Memory optimization patterns:")
    print("  ┌─────────────────────────────────┬───────────────────────────┐")
    print("  │ Pattern                         │ When to apply             │")
    print("  ├─────────────────────────────────┼───────────────────────────┤")
    print("  │ Generator instead of list       │ Single-pass iteration     │")
    print("  │ __slots__ on data classes       │ Many instances, small obj │")
    print("  │ Stream data instead of load all │ Large files, DB result    │")
    print("  │ numpy arrays for numeric data   │ Float/int arrays (10-100×)│")
    print("  │ del large objects immediately   │ Temp large collections    │")
    print("  └─────────────────────────────────┴───────────────────────────┘")


def main():
    demo_basics()
    demo_snapshot_comparison()
    demo_peak_memory()
    demo_optimization_table()


if __name__ == "__main__":
    main()

"""
02_cprofile_basics.py
======================
Running cProfile to attribute execution time to individual functions.

Topics:
  1. cProfile.Profile() — enable/disable in code
  2. pstats.Stats — loading, sorting, printing
  3. Columns: ncalls, tottime, percall, cumtime
  4. Saving and reloading .prof files

Run:
    python demo/module-07/02_cprofile_basics.py
"""

import cProfile
import pstats
import io
import re
import time


# ══════════════════════════════════════════════════════════════════════════════
# The code we want to profile — a simulated validation batch
#
# Deliberately slow version with three layered issues:
#   1. re.fullmatch called with raw string (re-compiles internally each time)
#   2. load_schema() simulates an expensive load called per record
#   3. _normalize() does a pure-Python character loop instead of str.lower()
#
# Profile output will show all three — we will fix them one at a time.
# ══════════════════════════════════════════════════════════════════════════════

def load_schema(schema_name: str) -> dict:
    """Simulate loading a JSON schema from disk — 0.2ms per call."""
    time.sleep(0.0002)
    return {"name": schema_name, "fields": ["email", "age", "country"]}


def _normalize(text: str) -> str:
    """Slow character-by-character lowercasing."""
    result = []
    for ch in text:
        if "A" <= ch <= "Z":
            result.append(chr(ord(ch) + 32))
        else:
            result.append(ch)
    return "".join(result)


def validate_record_slow(record: dict) -> bool:
    """
    Slow version — three deliberate bottlenecks:
      1. re.fullmatch with raw string (re-compiles pattern on every call)
      2. load_schema() called per record
      3. _normalize() instead of .lower()
    """
    schema = load_schema("user_schema")          # bottleneck 2: expensive per call
    email = _normalize(record.get("email", ""))  # bottleneck 3: slow normalise
    valid_email = re.fullmatch(                  # bottleneck 1: re-compile each call
        r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
        email,
    ) is not None
    return valid_email and len(record.get("name", "")) > 0


def make_records(n: int) -> list[dict]:
    return [
        {"email": f"user{i}@example.com", "name": f"User {i}"}
        for i in range(n)
    ]


# ══════════════════════════════════════════════════════════════════════════════
# PART 1: Running cProfile in code — the recommended pattern
#
# Steps:
#   profiler = cProfile.Profile()
#   profiler.enable()
#   ... your code ...
#   profiler.disable()
#   # now inspect with pstats
#
# Why wrap tightly? You only pay profiling overhead on the code path you care
# about.  Profiling the whole script includes import time and test setup.
# ══════════════════════════════════════════════════════════════════════════════

def demo_cprofile_in_code():
    print("=" * 60)
    print("PART 1: cProfile.Profile() — wrap a specific code path")
    print("=" * 60)
    print()

    records = make_records(200)

    profiler = cProfile.Profile()
    profiler.enable()

    results = [validate_record_slow(r) for r in records]

    profiler.disable()

    print(f"  Validated {len(records)} records — {sum(results)} passed")
    print()
    print("  Raw cProfile output (top 12 by cumulative time):")
    print()

    # pstats.Stats takes the profiler object and an output stream
    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.strip_dirs()               # remove path prefixes for readability
    stats.sort_stats("cumulative")   # cumtime = function + all sub-calls
    stats.print_stats(12)
    print(stream.getvalue())


# ══════════════════════════════════════════════════════════════════════════════
# PART 2: Reading the pstats columns
#
#    ncalls  tottime  percall  cumtime  percall  filename:lineno(function)
#
#   ncalls   — how many times the function was called
#   tottime  — time spent ONLY in this function (excludes sub-calls)
#   percall  — tottime / ncalls  (per-call cost of the function body)
#   cumtime  — tottime + time in ALL sub-calls  (full call tree cost)
#   percall  — cumtime / ncalls  (full per-call cost including sub-calls)
#
# First look: sort by cumtime.  The function at the top owns the most
# wall-clock time in its call tree.
# ══════════════════════════════════════════════════════════════════════════════

def demo_reading_columns():
    print("=" * 60)
    print("PART 2: Reading pstats columns — cumtime vs tottime")
    print("=" * 60)
    print()

    records = make_records(100)

    profiler = cProfile.Profile()
    profiler.enable()
    [validate_record_slow(r) for r in records]
    profiler.disable()

    # --- Sort by cumulative ---
    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.strip_dirs()
    stats.sort_stats("cumulative")
    stats.print_stats(8)
    output = stream.getvalue()

    # Annotate key lines
    print("  Sorted by cumtime (who owns the most total time?):")
    for line in output.splitlines():
        if "validate_record_slow" in line or "load_schema" in line or "ncalls" in line:
            print(f"  → {line}")
    print()

    # --- Sort by tottime ---
    stream2 = io.StringIO()
    stats2 = pstats.Stats(profiler, stream=stream2)
    stats2.strip_dirs()
    stats2.sort_stats("tottime")
    stats2.print_stats(8)
    output2 = stream2.getvalue()

    print("  Sorted by tottime (who does the most work in its own body?):")
    for line in output2.splitlines():
        if "_normalize" in line or "fullmatch" in line or "ncalls" in line:
            print(f"  → {line}")

    print()
    print("  Key rule:")
    print("    High cumtime + low tottime  → cost is in callees, drill down")
    print("    High tottime               → this function IS the bottleneck")


# ══════════════════════════════════════════════════════════════════════════════
# PART 3: Saving and reloading .prof files
#
# saving:  profiler.dump_stats("output.prof")
# loading: pstats.Stats("output.prof")
#
# Use cases:
#   - Share profiles with teammates
#   - Compare profiles from different runs (baseline vs optimized)
#   - Open in a GUI tool like snakeviz
# ══════════════════════════════════════════════════════════════════════════════

def demo_save_load_prof():
    import os
    import tempfile

    print("\n" + "=" * 60)
    print("PART 3: Saving and reloading .prof files")
    print("=" * 60)
    print()

    records = make_records(50)

    profiler = cProfile.Profile()
    profiler.enable()
    [validate_record_slow(r) for r in records]
    profiler.disable()

    # Save
    prof_path = os.path.join(tempfile.gettempdir(), "demo_validate.prof")
    profiler.dump_stats(prof_path)
    print(f"  Saved profile to: {prof_path}")

    # Reload and inspect
    stream = io.StringIO()
    loaded = pstats.Stats(prof_path, stream=stream)
    loaded.strip_dirs()
    loaded.sort_stats("cumulative")
    loaded.print_stats(5)

    print("  Reloaded from disk — top 5 by cumtime:")
    for line in stream.getvalue().splitlines()[6:12]:
        if line.strip():
            print(f"    {line}")

    print()
    print("  Tools that read .prof files:")
    print("    pstats (stdlib)  — command-line analysis")
    print("    snakeviz         — browser-based flamegraph  (pip install snakeviz)")
    print("    pyprof2calltree  — KCacheGrind format")

    os.remove(prof_path)


# ══════════════════════════════════════════════════════════════════════════════
# PART 4: print_callers() — tracing who calls the bottleneck
#
# Once you identify a slow function, find out what is calling it:
#   stats.print_callers("load_schema")
#
# This tells you how often each caller invokes the function,
# helping you understand whether batching or caching is the right fix.
# ══════════════════════════════════════════════════════════════════════════════

def demo_print_callers():
    print("\n" + "=" * 60)
    print("PART 4: print_callers() — who is calling the bottleneck?")
    print("=" * 60)
    print()

    records = make_records(50)

    profiler = cProfile.Profile()
    profiler.enable()
    [validate_record_slow(r) for r in records]
    profiler.disable()

    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.strip_dirs()
    stats.print_callers("load_schema")

    print("  Callers of load_schema (who is calling it and how many times?):")
    for line in stream.getvalue().splitlines():
        if line.strip():
            print(f"    {line}")

    print()
    print("  Interpretation: validate_record_slow calls load_schema once per")
    print("  record.  If ncalls = batch size, that function needs caching.")


def main():
    demo_cprofile_in_code()
    demo_reading_columns()
    demo_save_load_prof()
    demo_print_callers()


if __name__ == "__main__":
    main()

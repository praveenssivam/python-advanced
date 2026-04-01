"""
09_py_spy_simulation.py
========================
Understanding sampling profilers — demonstrating what py-spy shows.

py-spy is an external tool installed with: pip install py-spy
We can't run it in-process (it attaches to a PID from outside), but this
file simulates what its output looks like and demonstrates *how* to read it.

Topics:
  1. Deterministic (cProfile) vs sampling (py-spy) profiler comparison
  2. Simulating a "hot function" showing up in sampled stacks
  3. How to run py-spy in practice (commands + expected output)
  4. Reading a flame graph

Run:
    python demo/module-07/09_py_spy_simulation.py
"""

import cProfile
import pstats
import io
import time
import random
import sys


# ══════════════════════════════════════════════════════════════════════════════
# PART 1: Why cProfile can mislead for async/production code
#
# cProfile hooks every function call and return.  Overhead: 10–50%.
# py-spy samples the call stack N times/sec.  Overhead: <1%.
#
# For a long-running service, cProfile's overhead changes the behavior
# you are trying to observe.  py-spy is safe to attach to production.
#
# Both tools show the same hotspot for CPU-bound code:
#   → wide function = hot function
# ══════════════════════════════════════════════════════════════════════════════

def fast_util(n: int) -> int:
    """Fast utility — called many times but cheap per call."""
    return n * n


def medium_parser(text: str) -> list[str]:
    """Parser — moderate cost, called for each record."""
    return [word.strip() for word in text.split(",")]


def slow_validator(records: list[dict]) -> int:
    """
    Slow validator — the real hotspot.
    Simulates validation with an expensive regex-like scan.
    """
    count = 0
    for r in records:
        email = r.get("email", "")
        # Simulate expensive validation (counting characters, no regex)
        valid = (
            len(email) > 5 and
            "@" in email and
            email.index("@") > 0 and
            "." in email[email.index("@"):] and
            not email.startswith(".") and
            not email.endswith(".")
        )
        if valid:
            count += 1
        # Simulate extra work — intentional CPU burn
        _ = sum(ord(c) for c in email)
    return count


def run_pipeline(records: list[dict]) -> int:
    """Full pipeline — cProfile will show how time is distributed."""
    # Fast: call fast_util 10× per record
    for r in records:
        r["id_sq"] = fast_util(r["id"])

    # Medium: parse a tag field
    for r in records:
        r["tags"] = medium_parser(r.get("raw_tags", "a,b,c"))

    # Slow: validate emails — this is the bottleneck
    return slow_validator(records)


def demo_cprofile_comparison():
    print("=" * 60)
    print("PART 1: cProfile shows exact calls — deterministic")
    print("=" * 60)
    print()

    N = 2_000
    records = [
        {"id": i, "email": f"user{i}@example.com", "raw_tags": f"t{i},t{i+1},t{i+2}"}
        for i in range(N)
    ]

    profiler = cProfile.Profile()
    profiler.enable()
    result = run_pipeline(records)
    profiler.disable()

    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.strip_dirs()
    stats.sort_stats("tottime")
    stats.print_stats(8)
    raw = stream.getvalue()

    print(f"  Pipeline result: {result} valid records")
    print()
    print("  cProfile output (sorted by tottime — in-function CPU):")
    for line in raw.splitlines():
        if any(x in line for x in ["slow_", "medium_", "fast_", "run_pipe", "ncalls", "tottime"]):
            print(f"    {line}")

    print()
    print("  Observation: slow_validator has the highest tottime.")
    print("  fast_util has the highest ncalls but lowest tottime per call.")
    print()
    print("  This is what py-spy shows too — but via sampling instead of hooks:")
    print("  → if py-spy takes 100 samples and slow_validator is on the stack")
    print("    for 80 of them, its bar in 'py-spy top' occupies 80% of the view.")


# ══════════════════════════════════════════════════════════════════════════════
# PART 2: Simulating py-spy "top" output
#
# py-spy top shows a table like htop but for Python functions:
#   OwnTime   TotalTime   Function (filename:line)
#   80%       80%         slow_validator  (09_...:45)
#    8%        8%         medium_parser   (09_...:36)
#    4%        4%         fast_util       (09_...:28)
#
# OwnTime  = fraction of samples where this function was at the TOP of the stack
# TotalTime = fraction of samples where this function appeared ANYWHERE in stack
#
# Simulate by measuring relative time spent in each function.
# ══════════════════════════════════════════════════════════════════════════════

def demo_pyspy_simulation():
    print("\n" + "=" * 60)
    print("PART 2: What py-spy top would show")
    print("=" * 60)
    print()

    N = 1_000
    records = [
        {"id": i, "email": f"u{i}@example.com", "raw_tags": "a,b,c"}
        for i in range(N)
    ]

    # Measure each component separately
    import timeit

    t_fast   = timeit.timeit(lambda: [fast_util(r["id"]) for r in records], number=50) / 50
    t_medium = timeit.timeit(lambda: [medium_parser(r["raw_tags"]) for r in records], number=50) / 50
    t_slow   = timeit.timeit(lambda: slow_validator(records), number=20) / 20

    total = t_fast + t_medium + t_slow

    rows = [
        ("slow_validator",   t_slow,   records),
        ("medium_parser",    t_medium, records),
        ("fast_util",        t_fast,   records),
    ]
    rows.sort(key=lambda x: -x[1])

    print("  Simulated py-spy top output:")
    print()
    print(f"  {'OwnTime':>9}  {'Name':<25}  {'Location'}")
    print(f"  {'─'*9}  {'─'*25}  {'─'*35}")
    for name, t, _ in rows:
        pct = t / total * 100
        bar = "█" * int(pct / 3)
        print(f"  {pct:>8.1f}%  {name:<25}  09_py_spy_simulation.py")
    print()

    print("  How to run the real py-spy (requires external package):")
    print()
    print("    # Install (one time):")
    print("    pip install py-spy")
    print()
    print("    # Attach to a running process:")
    print("    py-spy top --pid <PID>")
    print()
    print("    # Run a script and record a flame graph:")
    print("    py-spy record -o profile.svg -- python my_service.py")
    print()
    print("    # Dump current call stacks (diagnose hangs):")
    print("    py-spy dump --pid <PID>")
    print()
    print("    # In Docker containers:")
    print("    docker run --cap-add SYS_PTRACE ...")


# ══════════════════════════════════════════════════════════════════════════════
# PART 3: Reading a flame graph (textual explanation)
#
# py-spy record -o profile.svg generates an SVG flame graph.
# This part explains how to read it — no SVG can be generated here,
# but the explanation maps to any flame graph tool.
# ══════════════════════════════════════════════════════════════════════════════

def demo_flame_graph_reading():
    print("\n" + "=" * 60)
    print("PART 3: Reading a flame graph")
    print("=" * 60)
    print()

    print("  ASCII representation of a flame graph (open SVG in browser):")
    print()
    print("  Time →")
    print("  ┌─────────────────────────────────────────────────────────────┐")
    print("  │                        main()                               │  100%")
    print("  ├──────────────────────────────────────────┬──────────────────┤")
    print("  │         run_pipeline()                   │  other code      │  100%")
    print("  ├────────────────────────┬────────┬────────┤                  │")
    print("  │   slow_validator()     │ medium │  fast  │                  │   68%")
    print("  ├───────┬────────────────┤ parser │  util  │                  │")
    print("  │ sum() │     loop       │        │        │                  │   68%")
    print("  └───────┴────────────────┴────────┴────────┴──────────────────┘")
    print()
    print("  Reading rules:")
    print()
    print("    X-axis = time fraction (WIDTH = % of total CPU time)")
    print("    Y-axis = call depth   (BOTTOM = entry point, TOP = leaf)")
    print()
    print("    Wide, flat top:  this function IS the CPU bottleneck")
    print("    Wide base only:  this function calls many different children")
    print("    Tall spike:      deep call chain — follow it to the wide top")
    print()
    print("  Pattern to look for (slow_validator):")
    print("    → Wide at the TOP of its call stack (own CPU time)")
    print("    → Clicking it in the browser shows file:lineno")
    print("    → Correlate with pstats tottime to confirm")
    print()
    print("  snakeviz provides an interactive equivalent from .prof files:")
    print("    pip install snakeviz")
    print("    snakeviz profile.prof")


# ══════════════════════════════════════════════════════════════════════════════
# PART 4: Deterministic vs sampling — choose the right tool
# ══════════════════════════════════════════════════════════════════════════════

def demo_tool_selection():
    print("\n" + "=" * 60)
    print("PART 4: Choosing the right profiler")
    print("=" * 60)
    print()
    print("  ┌───────────────────────────┬────────────────┬────────────────┐")
    print("  │ Situation                 │ Tool           │ Why            │")
    print("  ├───────────────────────────┼────────────────┼────────────────┤")
    print("  │ Dev — profile a function  │ cProfile       │ Exact counts   │")
    print("  │ Dev — visual hotspot      │ snakeviz       │ Flame graph    │")
    print("  │ Production CPU spike      │ py-spy top     │ No restart     │")
    print("  │ Production flame graph    │ py-spy record  │ <1% overhead   │")
    print("  │ Production hang/deadlock  │ py-spy dump    │ Stack snapshot │")
    print("  │ Memory allocation sites   │ tracemalloc    │ Stdlib, exact  │")
    print("  │ CI regression prevention  │ pytest-bench   │ Assertions     │")
    print("  └───────────────────────────┴────────────────┴────────────────┘")
    print()
    print("  Key difference: cProfile requires a process restart (or code wrap).")
    print("  py-spy attaches to any running PID — no restart, no code changes.")


def main():
    demo_cprofile_comparison()
    demo_pyspy_simulation()
    demo_flame_graph_reading()
    demo_tool_selection()


if __name__ == "__main__":
    main()

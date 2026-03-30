"""
03_regex_bottleneck.py
=======================
Identifying and fixing a regex re-compilation bottleneck.

Topics:
  1. How re.fullmatch / re.match compile patterns internally
  2. Profiling to see re._compile in the top ncalls
  3. Fix: move re.compile() to module level
  4. Before/after benchmark

Run:
    python demo/module-07/03_regex_bottleneck.py
"""

import cProfile
import pstats
import io
import re
import timeit


# ══════════════════════════════════════════════════════════════════════════════
# PART 1: What happens when you call re.fullmatch() with a raw string
#
# re.fullmatch(pattern, string) is NOT free — it:
#   1. Computes a hash of the pattern string
#   2. Looks up a compiled pattern in Python's internal cache (re._cache)
#   3. If cache miss: compiles the pattern to a DFA/NFA (expensive)
#   4. Runs the match
#
# Python's regex cache has a limited size (_MAXCACHE = 512).  In a hot loop
# with only one pattern this usually hits cache — but the hash computation
# and cache lookup still happen on EVERY call.
# Compiling at module level eliminates the entire lookup overhead.
# ══════════════════════════════════════════════════════════════════════════════

# --- BAD: raw string passed to fullmatch on every call ---

def validate_email_recompile(email: str) -> bool:
    """BAD: passes raw pattern string — cache lookup on every call."""
    return re.fullmatch(
        r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
        email,
    ) is not None


# --- GOOD: compile once at module level ---

_EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")

def validate_email_compiled(email: str) -> bool:
    """GOOD: uses pre-compiled pattern — zero compilation overhead."""
    return _EMAIL_PATTERN.fullmatch(email) is not None


# --- Test data ---
EMAILS = ["user@example.com", "bad.email", "another@domain.co.uk", "nope"] * 500
# 2,000 emails per batch


def demo_profile_recompile():
    print("=" * 60)
    print("PART 1: Profile showing re._compile in top ncalls")
    print("=" * 60)
    print()

    profiler = cProfile.Profile()
    profiler.enable()
    results = [validate_email_recompile(e) for e in EMAILS]
    profiler.disable()

    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.strip_dirs()
    stats.sort_stats("tottime")
    stats.print_stats(10)
    raw = stream.getvalue()

    print(f"  Validated {len(EMAILS):,} emails")
    print()
    print("  Top functions by tottime (re-compile version):")
    for line in raw.splitlines():
        if any(x in line for x in ["re", "fullmatch", "ncalls", "compile"]):
            print(f"    {line}")
    print()
    print("  Observation: re._compile or re.fullmatch appears with ncalls ≈ batch size.")
    print("  That means the pattern is being processed on every single call.")


def demo_profile_compiled():
    print("\n" + "=" * 60)
    print("PART 2: Profile after fixing — pattern compiled at module level")
    print("=" * 60)
    print()

    profiler = cProfile.Profile()
    profiler.enable()
    results = [validate_email_compiled(e) for e in EMAILS]
    profiler.disable()

    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.strip_dirs()
    stats.sort_stats("tottime")
    stats.print_stats(10)
    raw = stream.getvalue()

    print(f"  Validated {len(EMAILS):,} emails")
    print()
    print("  Top functions by tottime (compiled version):")
    for line in raw.splitlines():
        if any(x in line for x in ["re", "fullmatch", "ncalls", "validate"]):
            print(f"    {line}")
    print()
    print("  Observation: re overhead drops significantly.")
    print("  Most time is now in the match operation itself, not compilation.")


# ══════════════════════════════════════════════════════════════════════════════
# PART 3: Before/after benchmark
#
# Profile tells us WHERE.  timeit tells us HOW MUCH.
# Always confirm the improvement with a benchmark after fixing.
# ══════════════════════════════════════════════════════════════════════════════

def demo_benchmark():
    print("\n" + "=" * 60)
    print("PART 3: Before/after benchmark")
    print("=" * 60)
    print()

    number = 200

    slow_times = timeit.repeat(
        lambda: [validate_email_recompile(e) for e in EMAILS],
        number=number, repeat=5
    )
    fast_times = timeit.repeat(
        lambda: [validate_email_compiled(e) for e in EMAILS],
        number=number, repeat=5
    )

    slow_ms = min(slow_times) / number * 1000
    fast_ms = min(fast_times) / number * 1000
    speedup = slow_ms / fast_ms

    print(f"  Workload: {len(EMAILS):,} email validations per call")
    print()
    print(f"  BAD  (raw string each call):     {slow_ms:.3f}ms")
    print(f"  GOOD (pre-compiled at import):   {fast_ms:.3f}ms")
    print(f"  Speedup: {speedup:.1f}×")
    print()

    # Correctness check
    assert [validate_email_recompile(e) for e in EMAILS] == \
           [validate_email_compiled(e) for e in EMAILS], "Output mismatch!"
    print("  Correctness: ✓ outputs match")


# ══════════════════════════════════════════════════════════════════════════════
# PART 4: The pattern — how to spot and fix regex bottlenecks
#
# Detection:
#   - re._compile or re.fullmatch in top ncalls
#   - ncalls ≈ number of records/requests processed
#
# Fix:
#   - Move re.compile() to module level (or class-level __init__)
#   - For patterns with variables, use re.compile() with named groups
#
# Variants of the same mistake:
#   - re.match(pattern, text)   — same issue
#   - re.search(pattern, text)  — same issue
#   - re.sub(pattern, ...)      — same issue
# ══════════════════════════════════════════════════════════════════════════════

def demo_pattern_variants():
    print("\n" + "=" * 60)
    print("PART 4: Pattern variants — same issue, same fix")
    print("=" * 60)
    print()

    # All four variants — BAD vs GOOD
    examples = [
        ("re.match",    lambda t: re.match(r"\d{4}", t),
                        re.compile(r"\d{4}").match),
        ("re.search",   lambda t: re.search(r"@\w+\.\w+", t),
                        re.compile(r"@\w+\.\w+").search),
        ("re.fullmatch",lambda t: re.fullmatch(r"\w+@\w+\.\w+", t),
                        re.compile(r"\w+@\w+\.\w+").fullmatch),
        ("re.sub",      lambda t: re.sub(r"\s+", "-", t),
                        re.compile(r"\s+").sub),
    ]

    test_input = "user@example.com"
    print(f"  Test input: {test_input!r}")
    print()
    print(f"  {'Function':<15}  BAD (raw string)     GOOD (pre-compiled)")
    print(f"  {'─'*15}  {'─'*20}  {'─'*20}")

    for name, bad_fn, good_fn in examples:
        if name == "re.sub":
            bad_r  = bad_fn("hello   world")
            good_r = good_fn("-", "hello   world")
        else:
            bad_r  = bool(bad_fn(test_input))
            good_r = bool(good_fn(test_input))
        match = "✓" if bad_r == good_r else "✗"
        print(f"  {name:<15}  {str(bad_r):<20}  {str(good_r):<20}  {match}")

    print()
    print("  All four functions have the same fix: compile the pattern once.")


def main():
    demo_profile_recompile()
    demo_profile_compiled()
    demo_benchmark()
    demo_pattern_variants()


if __name__ == "__main__":
    main()

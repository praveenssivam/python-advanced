"""
01_timeit_benchmarking.py
==========================
Establishing reliable performance baselines with timeit.

Topics:
  1. timeit.timeit() — number, repeat, lambda vs stmt
  2. timeit.repeat() — removing variance, taking the minimum
  3. Comparing two implementations head-to-head
  4. Why you need a baseline before profiling

Run:
    python demo/module-07/01_timeit_benchmarking.py
"""

import timeit
import re


# ══════════════════════════════════════════════════════════════════════════════
# PART 1: timeit.timeit() — call count and timing
#
# timeit.timeit(stmt, number=N) runs stmt exactly N times and returns
# the TOTAL elapsed time in seconds.  Divide by N to get per-call time.
#
# Key design: timeit disables the garbage collector during the run so GC
# pauses don't corrupt measurements.  Always use perf_counter internally.
#
# number choice:
#   - Fast operations (ns–µs): number=100_000 or 1_000_000
#   - Medium (ms):             number=1_000
#   - Slow (>100ms):           number=10 or 5
# ══════════════════════════════════════════════════════════════════════════════

def slow_validate(emails: list[str]) -> list[bool]:
    """Re-compiles the regex on every call — the bottleneck we'll measure."""
    results = []
    for email in emails:
        results.append(re.fullmatch(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", email) is not None)
    return results


def fast_validate(emails: list[str]) -> list[bool]:
    """Pre-compiled regex — compiled once at definition time."""
    return [_EMAIL_RE.fullmatch(email) is not None for email in emails]


_EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")

SAMPLE_EMAILS = [
    "user@example.com",
    "bad-email",
    "another@domain.org",
    "not_valid",
    "test@sub.domain.co.uk",
] * 200   # 1,000 emails total


def demo_timeit_basics():
    print("=" * 60)
    print("PART 1: timeit.timeit() — establishing a baseline")
    print("=" * 60)
    print()

    # number=100 means: run the lambda 100 times, return total seconds
    number = 100
    total = timeit.timeit(lambda: slow_validate(SAMPLE_EMAILS), number=number)

    per_call_ms = (total / number) * 1000
    print(f"  slow_validate(1,000 emails) × {number} runs")
    print(f"  Total:    {total:.4f}s")
    print(f"  Per call: {per_call_ms:.3f}ms")
    print()
    print("  Interpretation:")
    print(f"    At {per_call_ms:.1f}ms per batch of 1,000,")
    print(f"    throughput ≈ {1000 / per_call_ms * 1000:.0f} emails/second")
    print()
    print("  This is your BASELINE — write it down before touching the code.")


# ══════════════════════════════════════════════════════════════════════════════
# PART 2: timeit.repeat() — removing noise with multiple samples
#
# A single timeit.timeit() call can include accidental spikes from OS
# scheduling, disk cache warming, etc.  repeat() runs the benchmark
# multiple times and gives you a list of totals.
#
# Rule: take the MINIMUM of repeat() results, not the mean.
#   - Minimum ≈ "best case under ideal conditions" — reproducible
#   - Mean includes OS noise — not reproducible across machines
#
# Python docs explicitly recommend: "take the minimum"
# ══════════════════════════════════════════════════════════════════════════════

def demo_repeat():
    print("\n" + "=" * 60)
    print("PART 2: timeit.repeat() — removing variance")
    print("=" * 60)
    print()

    number = 50
    repeat = 7

    samples = timeit.repeat(lambda: slow_validate(SAMPLE_EMAILS), number=number, repeat=repeat)
    per_call = [s / number * 1000 for s in samples]   # ms per call

    print(f"  {repeat} independent samples of {number} runs each:")
    for i, ms in enumerate(per_call, 1):
        bar = "█" * int(ms * 20)
        print(f"    sample {i}: {ms:6.3f}ms  {bar}")

    print()
    print(f"  min:   {min(per_call):.3f}ms  ← use this as your baseline")
    print(f"  max:   {max(per_call):.3f}ms  ← noisy outlier, ignore")
    print(f"  mean:  {sum(per_call)/len(per_call):.3f}ms  ← misleading, includes noise")
    print()
    print("  Rule: always take the minimum from repeat() for reliable baselines.")


# ══════════════════════════════════════════════════════════════════════════════
# PART 3: Head-to-head comparison
#
# The correct workflow:
#   1. Measure the slow implementation (baseline)
#   2. Measure the fast implementation (candidate)
#   3. Compute speedup ratio = baseline_min / candidate_min
#   4. Confirm correctness (same output)
#
# Never report speedup without also verifying correctness.
# ══════════════════════════════════════════════════════════════════════════════

def demo_comparison():
    print("\n" + "=" * 60)
    print("PART 3: Head-to-head comparison")
    print("=" * 60)
    print()

    number = 100

    slow_samples = timeit.repeat(lambda: slow_validate(SAMPLE_EMAILS), number=number, repeat=5)
    fast_samples = timeit.repeat(lambda: fast_validate(SAMPLE_EMAILS), number=number, repeat=5)

    slow_min_ms = min(slow_samples) / number * 1000
    fast_min_ms = min(fast_samples) / number * 1000
    speedup = slow_min_ms / fast_min_ms

    print(f"  Workload: {len(SAMPLE_EMAILS):,} email validations per call")
    print()
    print(f"  slow_validate (re-compile each call): {slow_min_ms:.3f}ms")
    print(f"  fast_validate (pre-compiled regex):   {fast_min_ms:.3f}ms")
    print(f"  Speedup: {speedup:.1f}×")
    print()

    # Verify correctness
    slow_out = slow_validate(SAMPLE_EMAILS)
    fast_out = fast_validate(SAMPLE_EMAILS)
    match = slow_out == fast_out
    print(f"  Outputs match: {match}  ← always verify before claiming improvement")
    print()
    print("  Next step: WHY is fast_validate faster?")
    print("  → cProfile will tell us exactly where the time goes.")


# ══════════════════════════════════════════════════════════════════════════════
# PART 4: Defining "fast enough"
#
# timeit gives you numbers.  Without a target, numbers are meaningless.
#
# SLA examples:
#   Real-time API endpoint:   p99 < 150ms
#   Batch pipeline per chunk: < 500ms per 10,000 records
#   Unit test suite total:    < 5s
#
# Workflow: observe slowness → define target → establish baseline →
#           profile → optimize → re-measure → compare to target
# ══════════════════════════════════════════════════════════════════════════════

def demo_sla_thinking():
    print("\n" + "=" * 60)
    print("PART 4: Defining 'fast enough'")
    print("=" * 60)
    print()

    number = 50
    total = timeit.timeit(lambda: fast_validate(SAMPLE_EMAILS), number=number)
    per_call_ms = total / number * 1000

    # Hypothetical SLA
    sla_ms = 5.0
    n_emails_per_call = len(SAMPLE_EMAILS)
    throughput = n_emails_per_call / (per_call_ms / 1000)

    print(f"  Current performance:  {per_call_ms:.3f}ms per {n_emails_per_call:,} emails")
    print(f"  Throughput:           {throughput:,.0f} emails/second")
    print()
    print(f"  SLA (hypothetical):   {sla_ms}ms per batch")
    status = "✓ PASS" if per_call_ms < sla_ms else "✗ FAIL"
    print(f"  Status:               {status}")
    print()
    print("  Key principle: define the target BEFORE profiling.")
    print("  Without a target you don't know when to stop optimizing.")


def main():
    demo_timeit_basics()
    demo_repeat()
    demo_comparison()
    demo_sla_thinking()


if __name__ == "__main__":
    main()

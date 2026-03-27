"""
05_asyncio_gather_patterns.py
==============================
Deep dive into asyncio.gather() — four patterns.

Pattern 1  Basic gather              — all succeed, results in input order
Pattern 2  Exception propagation     — one failure cancels everything (default)
Pattern 3  return_exceptions=True    — collect failures as values, keep going
Pattern 4  Nested gather + timeout   — wrap gather in wait_for for deadline

Run:
    python demo/day-06/05_asyncio_gather_patterns.py
"""

import asyncio
import time


# ══════════════════════════════════════════════════════════════════════════════
# Task variants
# ══════════════════════════════════════════════════════════════════════════════

async def success_task(task_id: int, delay: float = 0.1) -> dict:
    await asyncio.sleep(delay)
    return {"task_id": task_id, "status": "ok", "value": task_id * 10}


async def failing_task(task_id: int, delay: float = 0.05) -> dict:
    await asyncio.sleep(delay)
    raise ValueError(f"task {task_id}: simulated API error")


async def slow_task(task_id: int, delay: float = 2.0) -> dict:
    await asyncio.sleep(delay)
    return {"task_id": task_id, "status": "ok"}


# ══════════════════════════════════════════════════════════════════════════════
# PATTERN 1: Basic gather — all succeed
#
# gather(*coros) returns a list of results in the SAME ORDER as the inputs,
# regardless of the order they complete.
#
# This order guarantee is often critical:
#   results = await gather(get_user(id), get_orders(id), get_prefs(id))
#   user, orders, prefs = results   ← always correctly unpacked
# ══════════════════════════════════════════════════════════════════════════════

async def demo_basic_gather():
    print("=" * 60)
    print("PATTERN 1: Basic gather — all succeed, input order preserved")
    print("=" * 60)
    print()

    t0 = time.perf_counter()
    results = await asyncio.gather(
        success_task(0, 0.10),
        success_task(1, 0.05),   # finishes first, but still appears at index 1
        success_task(2, 0.15),
        success_task(3, 0.08),
        success_task(4, 0.12),
    )
    elapsed = time.perf_counter() - t0

    print("  Results (in INPUT order, even though completion order varied):")
    for i, r in enumerate(results):
        print(f"    index {i}  task_id={r['task_id']}  value={r['value']}")
    print(f"\n  Total: {elapsed:.3f}s  (bottleneck = 0.15s, not sum {0.10+0.05+0.15+0.08+0.12:.2f}s)")
    print()
    print("  ✓ Tuple unpacking works reliably:")
    r0, r1, r2, r3, r4 = results
    print(f"    r0={r0['value']}, r1={r1['value']}, r2={r2['value']}")


# ══════════════════════════════════════════════════════════════════════════════
# PATTERN 2: Exception propagation (default behaviour)
#
# If ANY coroutine raises, gather() re-raises that exception at the await site.
# Other coroutines that are still running ARE cancelled.
# Results from already-finished coroutines are lost.
#
# Use this when: all tasks must succeed or the whole operation is invalid.
# ══════════════════════════════════════════════════════════════════════════════

async def demo_exception_propagation():
    print("\n" + "=" * 60)
    print("PATTERN 2: Exception propagation (default) — one failure = all fail")
    print("=" * 60)
    print()

    try:
        results = await asyncio.gather(
            success_task(0, 0.10),
            failing_task(1, 0.05),   # raises after 0.05s
            success_task(2, 0.15),   # still running when failure hits
        )
    except ValueError as exc:
        print(f"  gather() raised: {exc}")
        print()
        print("  Task 0 finished OK but its result is LOST.")
        print("  Task 2 was cancelled because task 1 failed.")
        print()
        print("  When to accept this: 'all parts required' — e.g. transaction steps")


# ══════════════════════════════════════════════════════════════════════════════
# PATTERN 3: return_exceptions=True — partial success
#
# With return_exceptions=True, exceptions are returned as VALUES in the results
# list instead of being re-raised. All tasks run to completion regardless.
#
# Use this when: some tasks can fail without invalidating the others.
# ══════════════════════════════════════════════════════════════════════════════

async def demo_return_exceptions():
    print("\n" + "=" * 60)
    print("PATTERN 3: return_exceptions=True — partial success")
    print("=" * 60)
    print()

    t0 = time.perf_counter()
    results = await asyncio.gather(
        success_task(0, 0.10),
        failing_task(1, 0.05),   # exception becomes a value
        success_task(2, 0.08),
        failing_task(3, 0.12),   # another failure
        success_task(4, 0.10),
        return_exceptions=True,
    )
    elapsed = time.perf_counter() - t0

    successes = []
    failures  = []
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            failures.append((i, r))
            print(f"  index {i}: ERROR  → {type(r).__name__}: {r}")
        else:
            successes.append(r)
            print(f"  index {i}: OK     → task_id={r['task_id']}  value={r['value']}")

    print()
    print(f"  Succeeded: {len(successes)}   Failed: {len(failures)}")
    print(f"  Total: {elapsed:.3f}s  (all ran, even the failing ones)")
    print()
    print("  Production pattern: process successes, queue failures for retry.")


# ══════════════════════════════════════════════════════════════════════════════
# PATTERN 4: Gather with overall timeout
#
# asyncio.wait_for(awaitable, timeout=N) raises asyncio.TimeoutError after N
# seconds if the awaitable hasn't completed.
#
# Wrapping gather() in wait_for() applies a SINGLE deadline to the whole batch:
# if any task is slow enough to exceed it, the entire gather is cancelled.
#
# For per-task timeouts, wrap each coroutine individually in wait_for().
# ══════════════════════════════════════════════════════════════════════════════

async def demo_gather_timeout():
    print("\n" + "=" * 60)
    print("PATTERN 4: Gather wrapped in overall timeout")
    print("=" * 60)
    print()

    # --- Case A: all finish before deadline ---
    print("  Case A: all tasks finish within 0.5s deadline")
    try:
        results = await asyncio.wait_for(
            asyncio.gather(
                success_task(0, 0.10),
                success_task(1, 0.15),
                success_task(2, 0.20),
            ),
            timeout=0.5,
        )
        print(f"  → all {len(results)} results collected: {[r['value'] for r in results]}")
    except asyncio.TimeoutError:
        print("  → TimeoutError (unexpected)")

    # --- Case B: one task exceeds deadline ---
    print()
    print("  Case B: task 2 takes 2s but deadline is 0.3s")
    try:
        results = await asyncio.wait_for(
            asyncio.gather(
                success_task(0, 0.10),
                success_task(1, 0.15),
                slow_task(2, 2.00),    # this will trigger the timeout
            ),
            timeout=0.3,
        )
    except asyncio.TimeoutError:
        print("  → asyncio.TimeoutError: batch exceeded 0.3s deadline")
        print("  → tasks 0 and 1 completed but results are lost (gather cancelled)")

    # --- Case C: per-task timeout (each task has its own limit) ---
    print()
    print("  Case C: per-task timeouts (each task gets its own 0.3s window)")
    per_task_coros = [
        asyncio.wait_for(success_task(0, 0.10), timeout=0.3),
        asyncio.wait_for(success_task(1, 0.15), timeout=0.3),
        asyncio.wait_for(slow_task(2, 2.00),    timeout=0.3),  # only this one times out
    ]
    results = await asyncio.gather(*per_task_coros, return_exceptions=True)
    for i, r in enumerate(results):
        if isinstance(r, asyncio.TimeoutError):
            print(f"  task {i}: TIMEOUT")
        else:
            print(f"  task {i}: OK  value={r['value']}")

    print()
    print("  Per-task timeout + return_exceptions: most robust pattern.")


async def main():
    await demo_basic_gather()
    await demo_exception_propagation()
    await demo_return_exceptions()
    await demo_gather_timeout()

    print("\n" + "=" * 60)
    print("GATHER QUICK REFERENCE")
    print("=" * 60)
    print()
    print("  gather(*coros)                        all must succeed  → results list")
    print("  gather(*coros, return_exceptions=True) partial ok       → mix of results/exc")
    print("  wait_for(gather(*coros), timeout=N)   batch deadline    → TimeoutError if slow")
    print("  gather(*[wait_for(c,t) for c in ...]) per-task deadline → fine-grained")


if __name__ == "__main__":
    asyncio.run(main())

"""
02_asyncio_patterns.py
=======================
Four concurrency patterns for the same workload — side-by-side comparison.

Workload: fetch 3 data sources, each taking 0.1s.

Pattern 1  Sequential awaits       — simple, slow (0.3s)
Pattern 2  create_task() + await   — concurrent, fast (0.1s), explicit control
Pattern 3  asyncio.gather()        — concurrent, fast (0.1s), clean idiom
Pattern 4  asyncio.as_completed()  — concurrent, fast (0.1s), result on arrival

All four produce the same final result but differ in when results become
available and how much control you have over individual tasks.

Run:
    python demo/day-06/02_asyncio_patterns.py
"""

import asyncio
import time


# ══════════════════════════════════════════════════════════════════════════════
# Shared workload task
# ══════════════════════════════════════════════════════════════════════════════

async def fetch(source: str, delay: float = 0.1) -> dict:
    """Simulate fetching from an external source (DB, API, file)."""
    await asyncio.sleep(delay)
    return {"source": source, "rows": len(source) * 10}


SOURCES = [("users_db", 0.1), ("products_db", 0.1), ("orders_db", 0.1)]


# ══════════════════════════════════════════════════════════════════════════════
# PATTERN 1: Sequential awaits
#
# The event loop runs each coroutine to completion before starting the next.
# Simple to read, but latency adds up: 0.1 + 0.1 + 0.1 = 0.3s total.
#
# When to use:
#   - Result of task N is needed as INPUT to task N+1 (dependency chain)
#   - Only 1-2 tasks — overhead of task management not worth it
# ══════════════════════════════════════════════════════════════════════════════

async def pattern_sequential():
    print("─" * 50)
    print("PATTERN 1: Sequential awaits")
    print("─" * 50)

    t0 = time.perf_counter()
    results = []
    for source, delay in SOURCES:
        r = await fetch(source, delay)
        results.append(r)
        print(f"  [{time.perf_counter()-t0:.2f}s] got {r['source']}")

    elapsed = time.perf_counter() - t0
    print(f"\n  Total: {elapsed:.3f}s  (0.1 × 3 = 0.3s expected)\n")
    return results


# ══════════════════════════════════════════════════════════════════════════════
# PATTERN 2: create_task() + individual awaits
#
# asyncio.create_task(coro) schedules the coroutine IMMEDIATELY — it starts
# running the next time the event loop gets control (i.e. at the next await).
#
# Flow:
#   t=0.00  create_task(users)    — task queued, not yet running
#   t=0.00  create_task(products) — task queued
#   t=0.00  create_task(orders)   — task queued
#   t=0.00  await task_users      — event loop starts all 3 simultaneously
#   t=0.10  all 3 complete        — task_users result returned immediately
#
# When to use:
#   - You want to start a task in the background and await it later
#   - You need to cancel specific tasks individually
#   - You want to add tasks dynamically during execution
# ══════════════════════════════════════════════════════════════════════════════

async def pattern_create_task():
    print("─" * 50)
    print("PATTERN 2: create_task() + individual awaits")
    print("─" * 50)

    t0 = time.perf_counter()

    # All three tasks scheduled simultaneously — start running at first await
    task_users    = asyncio.create_task(fetch("users_db",    0.1))
    task_products = asyncio.create_task(fetch("products_db", 0.1))
    task_orders   = asyncio.create_task(fetch("orders_db",   0.1))

    print(f"  [{time.perf_counter()-t0:.2f}s] all 3 tasks created and scheduled")

    # Awaiting each — since they all started at the same time, they all finish
    # together, so await order here doesn't matter for total time
    r1 = await task_users
    r2 = await task_products
    r3 = await task_orders

    elapsed = time.perf_counter() - t0
    print(f"  [{elapsed:.2f}s] all results collected: "
          f"{r1['source']}, {r2['source']}, {r3['source']}")
    print(f"\n  Total: {elapsed:.3f}s  (all ran concurrently)\n")
    return [r1, r2, r3]


# ══════════════════════════════════════════════════════════════════════════════
# PATTERN 3: asyncio.gather()
#
# gather(*coros_or_tasks) schedules all, runs concurrently, and returns a
# list of results in INPUT ORDER (same order as the arguments).
#
# If any coroutine raises, the exception propagates from gather() by default.
# Use return_exceptions=True to collect exceptions as values (see file 05).
#
# When to use:
#   - Fan-out pattern: same work on N independent inputs
#   - You want results in a predictable order
#   - Standard concurrent fetch pattern
# ══════════════════════════════════════════════════════════════════════════════

async def pattern_gather():
    print("─" * 50)
    print("PATTERN 3: asyncio.gather()")
    print("─" * 50)

    t0 = time.perf_counter()

    results = await asyncio.gather(
        fetch("users_db",    0.1),
        fetch("products_db", 0.1),
        fetch("orders_db",   0.1),
    )

    elapsed = time.perf_counter() - t0
    for r in results:
        print(f"  {r['source']:15s}  rows={r['rows']}")
    print(f"\n  Total: {elapsed:.3f}s  (results in INPUT order)\n")
    return results


# ══════════════════════════════════════════════════════════════════════════════
# PATTERN 4: asyncio.as_completed()
#
# as_completed(coros) returns an iterator of futures in COMPLETION ORDER.
# Each iteration yields the next completed coroutine, allowing early processing.
#
# Unlike gather(), you don't wait for the slowest — you process each result
# the moment it arrives.
#
# When to use:
#   - Tasks have varying completion times
#   - You want to display progress or trigger follow-ups immediately
#   - "process the first 3 out of 10" type patterns
# ══════════════════════════════════════════════════════════════════════════════

async def pattern_as_completed():
    print("─" * 50)
    print("PATTERN 4: asyncio.as_completed()")
    print("─" * 50)

    # Different delays so completion order is visible
    coros = [
        fetch("orders_db",   0.30),   # slowest
        fetch("users_db",    0.10),   # fastest
        fetch("products_db", 0.20),   # middle
    ]

    t0 = time.perf_counter()
    results = []
    for fut in asyncio.as_completed(coros):
        r = await fut
        elapsed = time.perf_counter() - t0
        results.append(r)
        print(f"  [{elapsed:.2f}s] arrived: {r['source']}")

    elapsed = time.perf_counter() - t0
    print(f"\n  Total: {elapsed:.3f}s  (results in COMPLETION order)")
    print("  (note: orders_db (0.3s) finished last even though submitted first)\n")
    return results


async def main():
    print("Four Concurrency Patterns — same workload, different approaches")
    print()
    await pattern_sequential()
    await pattern_create_task()
    await pattern_gather()
    await pattern_as_completed()

    print("=" * 50)
    print("PATTERN COMPARISON")
    print("=" * 50)
    print()
    print("  Pattern              Time    Results order     Use when")
    print("  ──────────────────   ──────  ───────────────   ─────────")
    print("  Sequential awaits    0.30s   Input order       Dependencies between tasks")
    print("  create_task()        0.10s   Input order       Need to cancel/inspect tasks")
    print("  gather()             0.10s   Input order       Simple fan-out, predictable")
    print("  as_completed()       0.10s   Completion order  Process fast results early")


if __name__ == "__main__":
    asyncio.run(main())

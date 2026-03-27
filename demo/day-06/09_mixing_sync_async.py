"""
09_mixing_sync_async.py
========================
Bridging synchronous and asynchronous code safely.

Problems addressed:
  1. Blocking calls (time.sleep, CPU work) freeze the event loop
  2. run_in_executor() offloads blocking work to a thread/process pool
  3. Calling async code from synchronous contexts
  4. asyncio.run() vs loop.run_until_complete() (legacy)

Key rule: NEVER call time.sleep() or other blocking operations inside
          an async function — they block the entire event loop and
          prevent ALL other coroutines from running.

Run:
    python demo/day-06/09_mixing_sync_async.py
"""

import asyncio
import time
import concurrent.futures


# ══════════════════════════════════════════════════════════════════════════════
# PART 1: time.sleep() blocks the entire event loop
#
# When a coroutine calls time.sleep(1), it holds the GIL AND holds the
# event loop hostage — nothing else can run during that second.
#
# Anatomy of the freeze:
#   t=0.00  task_A starts, calls time.sleep(1)      ← EVENT LOOP FROZEN
#   t=1.00  time.sleep returns, event loop unfreezes
#   t=1.00  task_B can only start NOW (1s late)
#
# Expected with asyncio.sleep: task_A and task_B overlap → total ~0.1s
# Actual with time.sleep:      task_A then task_B sequential → total ~1.1s
# ══════════════════════════════════════════════════════════════════════════════

async def bad_async_task(name: str, delay: float) -> str:
    """BAD: uses time.sleep() — blocks event loop."""
    time.sleep(delay)             # ← blocks everything
    return f"{name} done"


async def good_async_task(name: str, delay: float) -> str:
    """GOOD: uses asyncio.sleep() — yields to event loop."""
    await asyncio.sleep(delay)    # ← cooperative, other tasks run during wait
    return f"{name} done"


async def demo_blocking_vs_async():
    print("=" * 60)
    print("PART 1: time.sleep() vs asyncio.sleep() in async code")
    print("=" * 60)
    print()

    # BAD: time.sleep blocks
    print("  BAD: two tasks using time.sleep(0.1)")
    t0 = time.perf_counter()
    r1, r2 = await asyncio.gather(
        bad_async_task("task-A", 0.1),
        bad_async_task("task-B", 0.1),
    )
    t_bad = time.perf_counter() - t0
    print(f"    {r1}, {r2}")
    print(f"    Time: {t_bad:.3f}s  ← 0.2s! Both blocked sequentially due to GIL hold")

    # GOOD: asyncio.sleep yields
    print()
    print("  GOOD: two tasks using asyncio.sleep(0.1)")
    t0 = time.perf_counter()
    r1, r2 = await asyncio.gather(
        good_async_task("task-A", 0.1),
        good_async_task("task-B", 0.1),
    )
    t_good = time.perf_counter() - t0
    print(f"    {r1}, {r2}")
    print(f"    Time: {t_good:.3f}s  ← 0.1s! Both ran concurrently")


# ══════════════════════════════════════════════════════════════════════════════
# PART 2: run_in_executor() — offload blocking work
#
# Sometimes you MUST call blocking code (legacy library, CPU work, file I/O):
#   loop.run_in_executor(executor, fn, *args)
#
# This submits fn(*args) to a thread or process pool, returning an awaitable.
# The event loop stays alive and can run other coroutines while fn executes
# in the background thread/process.
#
# Default executor: ThreadPoolExecutor (good for blocking I/O)
# Pass ProcessPoolExecutor for CPU-bound work.
# ══════════════════════════════════════════════════════════════════════════════

def blocking_file_read(path: str) -> str:
    """Synchronous file operation (legacy library or built-in open)."""
    time.sleep(0.15)   # simulate blocking disk I/O
    return f"contents of {path} (5000 bytes)"


def cpu_intensive(n: int) -> int:
    """CPU-bound synchronous computation."""
    return sum(i * i for i in range(n))


async def demo_run_in_executor():
    print("\n" + "=" * 60)
    print("PART 2: run_in_executor() — offload blocking calls")
    print("=" * 60)
    print()

    loop = asyncio.get_event_loop()

    # --- Thread executor for blocking I/O ---
    print("  Offloading 3 blocking file reads to thread executor:")
    t0 = time.perf_counter()

    # Run all three file reads concurrently in the thread pool
    r1, r2, r3 = await asyncio.gather(
        loop.run_in_executor(None, blocking_file_read, "/data/file1.csv"),
        loop.run_in_executor(None, blocking_file_read, "/data/file2.csv"),
        loop.run_in_executor(None, blocking_file_read, "/data/file3.csv"),
    )

    elapsed = time.perf_counter() - t0
    print(f"    file1: {r1[:30]}...")
    print(f"    file2: {r2[:30]}...")
    print(f"    file3: {r3[:30]}...")
    print(f"  Time: {elapsed:.3f}s  (all 3 overlapped in threads — not 0.45s)")

    # --- Process executor for CPU work ---
    print()
    print("  Offloading CPU computation to process executor:")
    proc_executor = concurrent.futures.ProcessPoolExecutor(max_workers=2)

    t0 = time.perf_counter()
    r1, r2 = await asyncio.gather(
        loop.run_in_executor(proc_executor, cpu_intensive, 3_000_000),
        loop.run_in_executor(proc_executor, cpu_intensive, 3_000_000),
    )
    elapsed = time.perf_counter() - t0
    proc_executor.shutdown(wait=False)

    print(f"    result1={r1:,}  result2={r2:,}")
    print(f"  Time: {elapsed:.3f}s  (2 processes ran in parallel, no GIL)")


# ══════════════════════════════════════════════════════════════════════════════
# PART 3: Calling async code from synchronous code
#
# Sometimes you're in a synchronous context (script, Django view, test) and
# need to run a coroutine. Options:
#
#   asyncio.run(coro)          — creates new loop, runs, closes  (Python 3.7+)
#   loop.run_until_complete()  — legacy, reuses an existing loop
#
# NEVER call asyncio.run() inside an already-running event loop
# (i.e. don't nest asyncio.run() calls).
# ══════════════════════════════════════════════════════════════════════════════

async def async_pipeline() -> list:
    """A complete async pipeline you want to call from sync code."""
    results = await asyncio.gather(
        good_async_task("fetch_users",    0.1),
        good_async_task("fetch_products", 0.1),
        good_async_task("fetch_orders",   0.1),
    )
    return results


def sync_orchestrator():
    """
    Synchronous function (e.g. a CLI script or a Django management command).
    Needs to run the async pipeline.
    """
    print("  [sync] calling async pipeline from synchronous code")
    t0 = time.perf_counter()
    results = asyncio.run(async_pipeline())   # blocks until pipeline completes
    elapsed = time.perf_counter() - t0
    print(f"  [sync] got {len(results)} results in {elapsed:.3f}s: {results}")
    return results


async def demo_sync_to_async():
    print("\n" + "=" * 60)
    print("PART 3: Calling async from sync code")
    print("=" * 60)
    print()
    print("  sync_orchestrator() calls asyncio.run() internally.")
    print("  It must run in a thread — asyncio.run() inside the")
    print("  running event loop would raise RuntimeError.")
    print()

    # Run the synchronous orchestrator in a thread so its asyncio.run()
    # call is made from a fresh thread (no running loop there).
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, sync_orchestrator)

    print()
    print("  Rule: asyncio.run() = one per program entry point.")
    print("  Never nest asyncio.run() inside a running loop.")
    print("  Inside an async context, always use await directly.")


# ══════════════════════════════════════════════════════════════════════════════
# PART 4: Decision guide — sync or async?
# ══════════════════════════════════════════════════════════════════════════════

async def demo_decision_guide():
    print("\n" + "=" * 60)
    print("PART 4: When to use what")
    print("=" * 60)
    print()
    print("  Inside async def:")
    print("  ─────────────────────────────────────────────────────────")
    print("  ✓ await asyncio.sleep(n)                   — async pause")
    print("  ✓ await some_async_lib.fetch(url)           — async I/O")
    print("  ✓ await loop.run_in_executor(None, fn, x)  — blocking → thread")
    print("  ✓ await loop.run_in_executor(proc, fn, x)  — CPU → process")
    print("  ✗ time.sleep(n)                            — freezes event loop")
    print("  ✗ requests.get(url)                        — blocks event loop")
    print("  ✗ open(path).read()                        — blocks for large files")
    print()
    print("  Accessing async code from sync:")
    print("  ─────────────────────────────────────────────────────────")
    print("  asyncio.run(coro)                 — clean, Python 3.7+")
    print("  loop.run_until_complete(coro)     — legacy, explicit loop management")
    print("  Never nest asyncio.run()          — RuntimeError")


async def main():
    await demo_blocking_vs_async()
    await demo_run_in_executor()
    await demo_sync_to_async()
    await demo_decision_guide()


if __name__ == "__main__":
    asyncio.run(main())

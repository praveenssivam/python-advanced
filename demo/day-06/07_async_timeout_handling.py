"""
07_async_timeout_handling.py
=============================
Timeout patterns in asyncio — four levels of granularity.

Topics:
  1. asyncio.wait_for()     — per-coroutine timeout (basic)
  2. Timeout on gather()    — batch deadline
  3. Per-task timeouts      — each task has its own limit
  4. Retry with backoff     — timeout + retry, production pattern

Run:
    python demo/day-06/07_async_timeout_handling.py
"""

import asyncio
import time


# ══════════════════════════════════════════════════════════════════════════════
# Tasks with varying completion times
# ══════════════════════════════════════════════════════════════════════════════

async def fast_task(task_id: int) -> dict:
    await asyncio.sleep(0.10)
    return {"task_id": task_id, "status": "completed", "took": 0.10}


async def slow_task(task_id: int) -> dict:
    """Simulates a hung/slow remote service."""
    await asyncio.sleep(2.0)
    return {"task_id": task_id, "status": "completed", "took": 2.0}


async def flaky_task(task_id: int, attempt: int = 1) -> dict:
    """Fails the first 2 attempts, succeeds on the 3rd."""
    if attempt <= 2:
        await asyncio.sleep(0.05)
        raise ConnectionError(f"task {task_id}: connection refused (attempt {attempt})")
    await asyncio.sleep(0.08)
    return {"task_id": task_id, "status": "ok", "attempt": attempt}


# ══════════════════════════════════════════════════════════════════════════════
# PART 1: asyncio.wait_for() — basic per-coroutine timeout
#
# wait_for(coro, timeout=N) wraps any awaitable with a deadline.
# If the awaitable doesn't complete within N seconds, the underlying coroutine
# is CANCELLED and asyncio.TimeoutError is raised.
#
# Crucial: the cancelled coroutine receives a CancelledError.
# If the coroutine has cleanup logic (try/finally), it runs during cancellation.
# ══════════════════════════════════════════════════════════════════════════════

async def demo_basic_timeout():
    print("=" * 60)
    print("PART 1: asyncio.wait_for() — per-coroutine timeout")
    print("=" * 60)
    print()

    # Case A: task completes before timeout
    print("  Case A: fast task (0.1s) with 0.5s timeout → completes")
    try:
        t0 = time.perf_counter()
        result = await asyncio.wait_for(fast_task(1), timeout=0.5)
        print(f"    ✓ result: {result}  (elapsed: {time.perf_counter()-t0:.3f}s)")
    except asyncio.TimeoutError:
        print("    ✗ timed out (unexpected)")

    # Case B: slow task exceeds timeout
    print()
    print("  Case B: slow task (2s) with 0.5s timeout → TimeoutError")
    try:
        t0 = time.perf_counter()
        result = await asyncio.wait_for(slow_task(2), timeout=0.5)
        print(f"    result: {result}")
    except asyncio.TimeoutError:
        elapsed = time.perf_counter() - t0
        print(f"    ✗ asyncio.TimeoutError after {elapsed:.3f}s")
        print(f"    Task 2 was cancelled (received CancelledError internally)")

    print()
    print("  Key: wait_for() CANCELS the wrapped coroutine — it does not just")
    print("  'abandon' it. Any finally blocks in the coroutine will run.")


# ══════════════════════════════════════════════════════════════════════════════
# PART 2: Timeout with catch and fallback
#
# Production pattern: on timeout, use a cached or default value rather than
# propagating the error to the caller.
# ══════════════════════════════════════════════════════════════════════════════

async def get_recommendations(user_id: int) -> list:
    """Slow ML service — may be too slow for real-time response."""
    await asyncio.sleep(1.5)
    return [f"item_{i}" for i in range(5)]


RECOMMENDATION_CACHE = {1: ["item_3", "item_7"], 2: ["item_1"]}


async def get_recommendations_with_fallback(user_id: int) -> dict:
    """Get recommendations with SLA protection + cache fallback."""
    try:
        recs = await asyncio.wait_for(get_recommendations(user_id), timeout=0.3)
        return {"source": "live", "items": recs}
    except asyncio.TimeoutError:
        cached = RECOMMENDATION_CACHE.get(user_id, [])
        return {"source": "cache_fallback", "items": cached}


async def demo_timeout_fallback():
    print("\n" + "=" * 60)
    print("PART 2: Timeout with cache fallback")
    print("=" * 60)
    print()
    print("  ML service takes 1.5s. SLA = 0.3s. Fall back to cached data.")
    print()

    for user_id in [1, 2]:
        t0 = time.perf_counter()
        result = await get_recommendations_with_fallback(user_id)
        elapsed = time.perf_counter() - t0
        print(f"  user {user_id}: source={result['source']:15s}  "
              f"items={result['items']}  ({elapsed:.3f}s)")

    print()
    print("  This pattern (timeout + stale data) is used in many real APIs:")
    print("  Facebook's Thundering Herd, Netflix's Hystrix, etc.")


# ══════════════════════════════════════════════════════════════════════════════
# PART 3: Per-task timeouts inside gather
#
# Wrapping each coroutine individually in wait_for() before passing to gather()
# gives each task its own independent timeout window.
# Failed tasks become TimeoutError values (with return_exceptions=True).
# ══════════════════════════════════════════════════════════════════════════════

async def demo_per_task_timeout():
    print("\n" + "=" * 60)
    print("PART 3: Per-task timeouts inside gather()")
    print("=" * 60)
    print()

    tasks_and_timeouts = [
        (fast_task(0), 0.5),   # OK
        (slow_task(1), 0.3),   # times out
        (fast_task(2), 0.5),   # OK
        (slow_task(3), 0.3),   # times out
        (fast_task(4), 0.5),   # OK
    ]

    t0 = time.perf_counter()
    results = await asyncio.gather(
        *[asyncio.wait_for(coro, timeout=tmo)
          for coro, tmo in tasks_and_timeouts],
        return_exceptions=True,
    )
    elapsed = time.perf_counter() - t0

    successes, timeouts = 0, 0
    for i, r in enumerate(results):
        if isinstance(r, asyncio.TimeoutError):
            timeouts += 1
            print(f"  task {i}: TIMEOUT")
        else:
            successes += 1
            print(f"  task {i}: OK  {r}")

    print(f"\n  {successes} succeeded, {timeouts} timed out  |  wall time: {elapsed:.3f}s")
    print("  Slow tasks timed out independently — fast tasks were unaffected.")


# ══════════════════════════════════════════════════════════════════════════════
# PART 4: Retry with exponential backoff
#
# Real services are flaky. The right pattern is: try → timeout → wait → retry.
# Each retry should wait longer than the last (exponential backoff) to avoid
# hammering an already-struggling service.
# ══════════════════════════════════════════════════════════════════════════════

async def with_retry(coro_factory, max_attempts: int = 3,
                     timeout: float = 0.5, base_delay: float = 0.1):
    """
    Retry a coroutine factory with timeout and exponential backoff.

    coro_factory: callable(attempt: int) -> coroutine
    """
    for attempt in range(1, max_attempts + 1):
        try:
            result = await asyncio.wait_for(coro_factory(attempt), timeout=timeout)
            return result
        except (asyncio.TimeoutError, ConnectionError) as exc:
            if attempt == max_attempts:
                raise
            delay = base_delay * (2 ** (attempt - 1))
            print(f"    attempt {attempt} failed ({type(exc).__name__}), "
                  f"retrying in {delay:.2f}s ...")
            await asyncio.sleep(delay)


async def demo_retry_backoff():
    print("\n" + "=" * 60)
    print("PART 4: Retry with exponential backoff")
    print("=" * 60)
    print()

    print("  flaky_task: fails attempt 1 and 2, succeeds on attempt 3")
    print()

    t0 = time.perf_counter()
    try:
        result = await with_retry(
            lambda attempt: flaky_task(42, attempt=attempt),
            max_attempts=3,
            timeout=0.5,
            base_delay=0.1,
        )
        elapsed = time.perf_counter() - t0
        print(f"  ✓ succeeded: {result}  ({elapsed:.3f}s total)")
    except Exception as exc:
        print(f"  ✗ all attempts failed: {exc}")


async def main():
    await demo_basic_timeout()
    await demo_timeout_fallback()
    await demo_per_task_timeout()
    await demo_retry_backoff()

    print("\n" + "=" * 60)
    print("TIMEOUT CHECKLIST")
    print("=" * 60)
    print()
    print("  ✓ Every external call should have a timeout — never await forever")
    print("  ✓ Use wait_for() for per-coroutine deadlines")
    print("  ✓ Wrap gather() in wait_for() for batch deadlines")
    print("  ✓ Per-task: [wait_for(c,t) for c ...] + return_exceptions=True")
    print("  ✓ Timeout ≠ cancel — ensure coroutines handle CancelledError cleanly")
    print("  ✓ Add retry + backoff for transient failures in production")


if __name__ == "__main__":
    asyncio.run(main())

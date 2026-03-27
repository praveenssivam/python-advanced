"""
08_async_semaphore_rate_limiting.py
=====================================
asyncio.Semaphore — control concurrency and protect shared resources.

Topics:
  1. Semaphore basics — limit simultaneous access
  2. Without semaphore — all 20 tasks start at once (resource exhaustion)
  3. With semaphore — max 5 run at a time (controlled batching)
  4. Rate limiting — tasks per second, not just tasks at once
  5. Circuit breaker pattern — pause when errors exceed a threshold

Run:
    python demo/day-06/08_async_semaphore_rate_limiting.py
"""

import asyncio
import time
import collections


# ══════════════════════════════════════════════════════════════════════════════
# Simulated external resource
# ══════════════════════════════════════════════════════════════════════════════

_active_connections = 0
_peak_connections   = 0


async def external_api_call(task_id: int) -> dict:
    """Simulate an external API call. Tracks active connection count."""
    global _active_connections, _peak_connections
    _active_connections += 1
    _peak_connections = max(_peak_connections, _active_connections)
    try:
        await asyncio.sleep(0.1)   # simulate network latency
        return {"task_id": task_id, "status": "ok"}
    finally:
        _active_connections -= 1


def reset_counters():
    global _active_connections, _peak_connections
    _active_connections = 0
    _peak_connections = 0


# ══════════════════════════════════════════════════════════════════════════════
# PART 1: Without semaphore — all tasks start simultaneously
#
# 20 tasks × 0.1s = total 0.1s (great speed), but all 20 connections open
# at once. Under real conditions this would:
#   - Exhaust a connection pool (max 5-25 connections in most DBs)
#   - Hit API rate limits
#   - Overload a service (thundering herd on startup)
# ══════════════════════════════════════════════════════════════════════════════

async def demo_no_semaphore():
    print("=" * 60)
    print("PART 1: Without semaphore — unbounded concurrency")
    print("=" * 60)
    print()

    n = 20
    reset_counters()

    t0 = time.perf_counter()
    results = await asyncio.gather(*[external_api_call(i) for i in range(n)])
    elapsed = time.perf_counter() - t0

    print(f"  {n} tasks, all started simultaneously")
    print(f"  Total time:       {elapsed:.3f}s")
    print(f"  Peak connections: {_peak_connections}  ← all {n} open at once")
    print()
    print("  Fast, but dangerous: DB connection pools typically max out at 5-25.")
    print("  Real-world result: ConnectionPoolExhausted or HTTP 429 Too Many Requests")


# ══════════════════════════════════════════════════════════════════════════════
# PART 2: With semaphore — controlled concurrency
#
# asyncio.Semaphore(N) allows at most N coroutines inside 'async with sem:' at once.
# Others block at the 'async with' until a slot opens.
#
# Flow with Semaphore(5) and 20 tasks:
#   batch 1: tasks 0-4  start at t=0.00, finish at t=0.10
#   batch 2: tasks 5-9  start at t=0.10, finish at t=0.20
#   batch 3: tasks 10-14 ...
#   batch 4: tasks 15-19 ...
#   Total: 4 batches × 0.1s = 0.40s
# ══════════════════════════════════════════════════════════════════════════════

async def demo_with_semaphore():
    print("\n" + "=" * 60)
    print("PART 2: With asyncio.Semaphore(5) — max 5 concurrent")
    print("=" * 60)
    print()

    n = 20
    sem = asyncio.Semaphore(5)
    reset_counters()

    active_timeline = []

    async def rate_limited_call(task_id: int) -> dict:
        async with sem:    # blocks here if 5 slots are already taken
            result = await external_api_call(task_id)
            active_timeline.append((task_id, _active_connections))
            return result

    t0 = time.perf_counter()
    results = await asyncio.gather(*[rate_limited_call(i) for i in range(n)])
    elapsed = time.perf_counter() - t0

    print(f"  {n} tasks with Semaphore(5)")
    print(f"  Total time:       {elapsed:.3f}s  (4 batches × 0.1s = 0.4s expected)")
    print(f"  Peak connections: {_peak_connections}  ← never exceeded 5")
    print()
    print("  Slower than unbounded, but safe for the downstream service.")
    print("  Connection pool stays within limits; no rate limit errors.")


# ══════════════════════════════════════════════════════════════════════════════
# PART 3: Visualising batch execution
#
# Each task prints when it starts and finishes, making the batching visible.
# ══════════════════════════════════════════════════════════════════════════════

async def demo_visualised():
    print("\n" + "=" * 60)
    print("PART 3: Visualised batch execution (10 tasks, sem=3)")
    print("=" * 60)
    print()

    sem = asyncio.Semaphore(3)
    t0 = time.perf_counter()

    async def tracked_call(task_id: int) -> dict:
        async with sem:
            start = time.perf_counter() - t0
            print(f"  [{start:.2f}s] START  task {task_id:2d}  "
                  f"(sem slots in use: {3 - sem._value}/3)")
            await asyncio.sleep(0.1)
            end = time.perf_counter() - t0
            print(f"  [{end:.2f}s] DONE   task {task_id:2d}")
            return {"task_id": task_id}

    results = await asyncio.gather(*[tracked_call(i) for i in range(10)])
    elapsed = time.perf_counter() - t0
    print(f"\n  Total: {elapsed:.3f}s  (10 tasks / 3 concurrent = ~4 batches × 0.1s)")


# ══════════════════════════════════════════════════════════════════════════════
# PART 4: Token-bucket rate limiter (tasks per second)
#
# Semaphore limits CONCURRENT tasks. Sometimes you need to limit
# THROUGHPUT: e.g. "no more than 10 calls per second" (API rate limit).
#
# Simple approach: release one permit per second using a background task.
# ══════════════════════════════════════════════════════════════════════════════

class RateLimiter:
    """
    Token-bucket rate limiter: allows up to `rate` calls per second.
    Uses a Semaphore and a background task that refills the bucket.
    """
    def __init__(self, rate: int):
        self._rate = rate
        self._sem = asyncio.Semaphore(rate)

    async def __aenter__(self):
        await self._sem.acquire()
        return self

    async def __aexit__(self, *_):
        # Release after 1/rate seconds — ensures max `rate` per second
        asyncio.get_event_loop().call_later(1.0 / self._rate, self._sem.release)


async def demo_rate_limiting():
    print("\n" + "=" * 60)
    print("PART 4: Rate limiting — max 5 calls per second")
    print("=" * 60)
    print()

    limiter = RateLimiter(rate=5)
    timestamps = []

    async def rate_limited_request(i: int):
        async with limiter:
            ts = time.perf_counter()
            timestamps.append(ts)
            return i

    t0 = time.perf_counter()
    results = await asyncio.gather(*[rate_limited_request(i) for i in range(15)])
    elapsed = time.perf_counter() - t0

    # Group timestamps into 0.2s windows to show rate
    buckets = collections.defaultdict(int)
    for ts in timestamps:
        bucket = int((ts - t0) * 5)   # 5 buckets per second
        buckets[bucket] += 1

    print(f"  15 requests at max 5 req/s:")
    for bucket, count in sorted(buckets.items()):
        bar = "█" * count
        print(f"    t≈{bucket*0.2:.1f}s  [{bar}] {count} calls")
    print(f"\n  Total: {elapsed:.3f}s  (15 calls at 5/s = 3s minimum)")


async def main():
    await demo_no_semaphore()
    await demo_with_semaphore()
    await demo_visualised()
    await demo_rate_limiting()

    print("\n" + "=" * 60)
    print("SEMAPHORE QUICK REFERENCE")
    print("=" * 60)
    print()
    print("  asyncio.Semaphore(N)         → allow N concurrent holders")
    print("  async with sem:              → acquire on enter, release on exit")
    print("  sem._value                   → current free slots (debug only)")
    print()
    print("  Use cases:")
    print("    Semaphore(pool_size)     → match DB connection pool limit")
    print("    Semaphore(1)             → mutex (same as asyncio.Lock)")
    print("    RateLimiter(n)           → N requests per second")
    print("    Semaphore(5) in gather() → controlled fan-out (throttling)")


if __name__ == "__main__":
    asyncio.run(main())

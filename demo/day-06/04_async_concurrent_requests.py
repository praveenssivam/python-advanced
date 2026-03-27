"""
04_async_concurrent_requests.py
=================================
Simulating 10 concurrent HTTP requests with asyncio.

Demonstrates:
  - Sequential async (still slow — each request waits for the previous)
  - Truly concurrent async (gather sends all at once)
  - Progress tracking with as_completed()
  - Mixing fast and slow endpoints

Key lesson: async alone doesn't make things concurrent.
You must USE gather() or create_task() — sequential awaits are just as slow
as synchronous code.

Run:
    python demo/day-06/04_async_concurrent_requests.py
"""

import asyncio
import time


# ══════════════════════════════════════════════════════════════════════════════
# Simulated HTTP client
# ══════════════════════════════════════════════════════════════════════════════

async def http_get(url: str, latency: float = 0.1) -> dict:
    """
    Simulate an HTTP GET request with realistic latency.
    Production equivalent: async with aiohttp.ClientSession() as session:
                               async with session.get(url) as resp:
                                   return await resp.json()
    """
    await asyncio.sleep(latency)
    return {
        "url": url,
        "status": 200,
        "body": f"data from {url.split('/')[-1]}",
        "latency": latency,
    }


ENDPOINTS = [f"https://api.example.com/resource/{i}" for i in range(10)]


# ══════════════════════════════════════════════════════════════════════════════
# APPROACH 1: Sequential async — the WRONG way to do "parallel" requests
#
# Each `await http_get(...)` suspends this coroutine and waits for the result.
# No other coroutines for these requests have been created, so they execute
# one at a time. Total time = 10 × 0.1s = 1.0s.
#
# This is the most common async mistake: using await inside a for-loop
# and expecting parallelism.
# ══════════════════════════════════════════════════════════════════════════════

async def fetch_sequential() -> list:
    print("=" * 60)
    print("APPROACH 1: Sequential async (await in a loop)")
    print("=" * 60)
    print()

    t0 = time.perf_counter()
    results = []
    for url in ENDPOINTS:
        r = await http_get(url)
        results.append(r)
        print(f"  [{time.perf_counter()-t0:.2f}s] ← {r['url'].split('/')[-1]}")

    elapsed = time.perf_counter() - t0
    print(f"\n  Total: {elapsed:.3f}s  (10 × 0.1s — no concurrency!)")
    print("  Even though this is async code, 'await' in a loop is sequential.")
    return results


# ══════════════════════════════════════════════════════════════════════════════
# APPROACH 2: Concurrent with gather() — the RIGHT way
#
# asyncio.gather() submits ALL coroutines to the event loop simultaneously.
# Each coroutine runs until it hits an await, then yields, letting others run.
# Total time ≈ max(individual times) ≈ 0.1s.
# ══════════════════════════════════════════════════════════════════════════════

async def fetch_concurrent_gather() -> list:
    print("\n" + "=" * 60)
    print("APPROACH 2: Concurrent with asyncio.gather()")
    print("=" * 60)
    print()

    t0 = time.perf_counter()
    results = await asyncio.gather(*[http_get(url) for url in ENDPOINTS])
    elapsed = time.perf_counter() - t0

    for r in results:
        print(f"  {r['url'].split('/')[-1]:12s}  status={r['status']}")
    print(f"\n  Total: {elapsed:.3f}s  (all 10 requests overlapped)")
    print(f"  Speedup: {1.0/elapsed:.0f}×  versus sequential")
    return results


# ══════════════════════════════════════════════════════════════════════════════
# APPROACH 3: as_completed() with progress tracking
#
# When endpoints have different latencies, as_completed() lets you process
# results as soon as they arrive. Useful for:
#   - Showing progress indicators
#   - Returning "first successful response" (cancel the rest)
#   - Accumulating partial results before all finish
# ══════════════════════════════════════════════════════════════════════════════

async def fetch_with_progress() -> list:
    print("\n" + "=" * 60)
    print("APPROACH 3: as_completed() — progress tracking")
    print("=" * 60)
    print()

    # Give endpoints varied latencies to make order visible
    import random
    random.seed(42)
    coros = [http_get(url, latency=round(0.05 + random.random() * 0.15, 3))
             for url in ENDPOINTS]

    t0 = time.perf_counter()
    results = []
    completed = 0
    for fut in asyncio.as_completed(coros):
        r = await fut
        completed += 1
        elapsed = time.perf_counter() - t0
        bar = "█" * completed + "░" * (len(ENDPOINTS) - completed)
        print(f"  [{elapsed:.2f}s]  [{bar}]  {completed}/{len(ENDPOINTS)}  "
              f"← {r['url'].split('/')[-1]} ({r['latency']:.3f}s)")
        results.append(r)

    elapsed = time.perf_counter() - t0
    print(f"\n  Total: {elapsed:.3f}s  (results processed on arrival)")
    return results


# ══════════════════════════════════════════════════════════════════════════════
# APPROACH 4: create_task() + cancel slow ones
#
# Sometimes you want the first N results and don't care about the rest.
# create_task() gives you Future-like handles you can cancel.
# ══════════════════════════════════════════════════════════════════════════════

async def fetch_first_three() -> list:
    print("\n" + "=" * 60)
    print("APPROACH 4: create_task() — take first 3, cancel the rest")
    print("=" * 60)
    print()

    # Simulate endpoints with high variance in response time
    latencies = [0.30, 0.05, 0.20, 0.08, 0.35, 0.12, 0.25, 0.04, 0.18, 0.40]
    tasks = [
        asyncio.create_task(http_get(ENDPOINTS[i], latencies[i]))
        for i in range(len(ENDPOINTS))
    ]

    t0 = time.perf_counter()
    results = []
    for fut in asyncio.as_completed(tasks):
        r = await fut
        results.append(r)
        elapsed = time.perf_counter() - t0
        print(f"  [{elapsed:.2f}s] result #{len(results)}: "
              f"{r['url'].split('/')[-1]} (latency={r['latency']:.2f}s)")
        if len(results) == 3:
            # Cancel remaining tasks — we have what we need
            cancelled = sum(1 for t in tasks if t.cancel())
            print(f"\n  Got 3 results — cancelling {cancelled} remaining tasks")
            break

    elapsed = time.perf_counter() - t0
    print(f"  Done in {elapsed:.3f}s  (only waited for 3 fastest responses)")
    return results


async def main():
    await fetch_sequential()
    await fetch_concurrent_gather()
    await fetch_with_progress()
    await fetch_first_three()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print()
    print("  'async def' alone does NOT create concurrency.")
    print("  You need gather() or create_task() to run tasks concurrently.")
    print()
    print("  Approach           When to use")
    print("  ─────────────────  ──────────────────────────────────────")
    print("  await in a loop    Tasks depend on previous result")
    print("  gather()           All results needed, don't care about order")
    print("  as_completed()     Process results as they arrive (progress)")
    print("  create_task()      Need handles to cancel/inspect tasks")


if __name__ == "__main__":
    asyncio.run(main())

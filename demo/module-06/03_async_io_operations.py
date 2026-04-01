"""
03_async_io_operations.py
==========================
Simulating the three I/O types without external libraries.

Real-world I/O:
  Network  → HTTP calls, database queries, message queue polling
  File     → reading large files from disk (with aiofiles in production)
  Database → ORM queries (with asyncpg, SQLAlchemy async, etc.)

This file simulates all three using asyncio.sleep() as the I/O stand-in,
showing non-blocking behaviour and how 5 concurrent operations complete
in the time it takes to do just one.

Run:
    python demo/module-06/03_async_io_operations.py
"""

import asyncio
import time
import random


# ══════════════════════════════════════════════════════════════════════════════
# Simulated I/O coroutines
# Each represents a different type of I/O operation.
# In production these would use async libraries (aiohttp, aiofiles, asyncpg).
# ══════════════════════════════════════════════════════════════════════════════

async def network_request(url: str, latency: float = 0.10) -> dict:
    """
    Simulates an async HTTP GET.
    Production: aiohttp.ClientSession.get(url)
    """
    await asyncio.sleep(latency)
    return {"type": "network", "url": url, "status": 200, "bytes": 1024}


async def file_read(path: str, latency: float = 0.08) -> dict:
    """
    Simulates async file read.
    Production: aiofiles.open(path).read()
    """
    await asyncio.sleep(latency)
    return {"type": "file", "path": path, "lines": 5000, "size_kb": 180}


async def db_query(query: str, latency: float = 0.12) -> dict:
    """
    Simulates an async database query.
    Production: asyncpg.Connection.fetch(query)
    """
    await asyncio.sleep(latency)
    return {"type": "database", "query": query, "rows": 42, "latency_ms": latency * 1000}


# ══════════════════════════════════════════════════════════════════════════════
# PART 1: Each I/O type run individually
# Shows baseline timing for each kind of operation.
# ══════════════════════════════════════════════════════════════════════════════

async def demo_individual():
    print("=" * 60)
    print("PART 1: Individual I/O operations")
    print("=" * 60)
    print()

    ops = [
        ("Network", network_request("https://api.example.com/users")),
        ("File",    file_read("/data/records.csv")),
        ("DB",      db_query("SELECT * FROM orders WHERE status='pending'")),
    ]

    for label, coro in ops:
        t0 = time.perf_counter()
        result = await coro
        elapsed = time.perf_counter() - t0
        print(f"  {label:8s}: {elapsed:.3f}s  → {result}")

    print()
    print("  If run sequentially: 0.10 + 0.08 + 0.12 = 0.30s total")


# ══════════════════════════════════════════════════════════════════════════════
# PART 2: All three run concurrently
# Non-blocking: while network_request sleeps, file_read and db_query also run.
# Total time = max(0.10, 0.08, 0.12) = 0.12s, not sum.
# ══════════════════════════════════════════════════════════════════════════════

async def demo_concurrent_trio():
    print("\n" + "=" * 60)
    print("PART 2: All three I/O types run concurrently")
    print("=" * 60)
    print()

    t0 = time.perf_counter()

    net_r, file_r, db_r = await asyncio.gather(
        network_request("https://api.example.com/users"),
        file_read("/data/records.csv"),
        db_query("SELECT * FROM orders WHERE status='pending'"),
    )

    elapsed = time.perf_counter() - t0
    print(f"  Network :  {net_r['url']}  → {net_r['status']}")
    print(f"  File    :  {file_r['path']}  → {file_r['lines']} lines")
    print(f"  Database:  {db_r['rows']} rows")
    print()
    print(f"  Total: {elapsed:.3f}s  (bottleneck = slowest op = 0.12s)")
    print(f"  Sequential would have taken: 0.30s")
    print(f"  Speedup: {0.30 / elapsed:.1f}×")


# ══════════════════════════════════════════════════════════════════════════════
# PART 3: 5 mixed operations run concurrently
# Demonstrates that async scales linearly — 5 ops still ~0.12s, not 0.6s.
# ══════════════════════════════════════════════════════════════════════════════

async def mixed_operation(op_id: int) -> dict:
    """Pick a random I/O type and run it."""
    op_type = op_id % 3
    if op_type == 0:
        result = await network_request(f"https://api.example.com/item/{op_id}", 0.10)
    elif op_type == 1:
        result = await file_read(f"/data/shard_{op_id}.parquet", 0.08)
    else:
        result = await db_query(f"SELECT * FROM table_x WHERE id={op_id}", 0.12)
    result["op_id"] = op_id
    return result


async def demo_five_concurrent():
    print("\n" + "=" * 60)
    print("PART 3: 5 mixed operations — all concurrent")
    print("=" * 60)
    print()
    print("  Op types: 0,3=network(0.10s)  1,4=file(0.08s)  2=db(0.12s)")
    print()

    t0 = time.perf_counter()
    results = await asyncio.gather(*[mixed_operation(i) for i in range(5)])
    elapsed = time.perf_counter() - t0

    for r in results:
        print(f"  op {r['op_id']}  type={r['type']:8s}  → status/rows/lines={r.get('status') or r.get('rows') or r.get('lines')}")

    print()
    print(f"  Total: {elapsed:.3f}s  (max latency = 0.12s from DB ops)")
    print(f"  Sequential would have been: {0.10*2 + 0.08*2 + 0.12:.2f}s")
    print(f"  'All 5 operations completed in {elapsed:.2f}s  ← same as doing just one'")


# ══════════════════════════════════════════════════════════════════════════════
# PART 4: Scaling up — 20 operations, still ~0.12s
# This demonstrates why async is ideal for I/O-heavy microservices.
# More tasks don't increase wall time as long as the event loop isn't starved.
# ══════════════════════════════════════════════════════════════════════════════

async def demo_scaling():
    print("\n" + "=" * 60)
    print("PART 4: Scaling — 20 operations concurrently")
    print("=" * 60)
    print()

    n = 20
    t0 = time.perf_counter()
    results = await asyncio.gather(*[mixed_operation(i) for i in range(n)])
    elapsed = time.perf_counter() - t0

    counts = {"network": 0, "file": 0, "database": 0}
    for r in results:
        counts[r["type"]] += 1

    print(f"  {n} operations: {counts}")
    print(f"  Total: {elapsed:.3f}s  (still bottlenecked by 0.12s, not by count)")
    print()
    print("  Compare with threads (Module 5):")
    print("  Threads: 20 ops also take ~0.12s, but each thread = 1-2 MB RAM")
    print("  Async:   20 ops take ~0.12s, coroutines = ~1-2 KB RAM each")
    print("  At 10,000 concurrent connections: async uses ~100× less memory.")


async def main():
    await demo_individual()
    await demo_concurrent_trio()
    await demo_five_concurrent()
    await demo_scaling()


if __name__ == "__main__":
    asyncio.run(main())

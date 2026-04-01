"""
06_async_context_managers.py
=============================
Async context managers with __aenter__ and __aexit__.

Topics:
  1. Why async resources need async context managers
  2. Implementing __aenter__ / __aexit__ in a class
  3. Using @asynccontextmanager decorator (generator style)
  4. Cleanup guarantee — __aexit__ always runs, even on exception
  5. Real-world pattern: async database connection pool

Run:
    python demo/module-06/06_async_context_managers.py
"""

import asyncio
import time
from contextlib import asynccontextmanager


# ══════════════════════════════════════════════════════════════════════════════
# PART 1: Class-based async context manager
#
# A regular context manager uses __enter__ / __exit__ (synchronous).
# An ASYNC context manager uses __aenter__ / __aexit__ (coroutines).
#
# Why async?  Because I/O operations (open connection, handshake, close) must
# suspend without blocking — they need to be awaitable.
#
# Syntax:  async with Resource() as r:
#              await r.query(...)
# ══════════════════════════════════════════════════════════════════════════════

class AsyncDatabase:
    """
    Simulated async database connection.
    In production this would wrap asyncpg.connect() / pool.acquire().
    """

    def __init__(self, dsn: str):
        self.dsn = dsn
        self._connection = None
        self._query_count = 0

    async def __aenter__(self) -> "AsyncDatabase":
        print(f"    [__aenter__] connecting to {self.dsn} ...")
        await asyncio.sleep(0.05)   # simulate connection handshake
        self._connection = f"conn://{self.dsn}"
        print(f"    [__aenter__] connected: {self._connection}")
        return self              # self is bound to the 'as' variable

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        print(f"    [__aexit__]  closing connection (queries run: {self._query_count})")
        await asyncio.sleep(0.02)  # simulate graceful disconnect
        self._connection = None
        if exc_type is not None:
            print(f"    [__aexit__]  exception during session: {exc_type.__name__}: {exc_val}")
        print(f"    [__aexit__]  connection closed cleanly")
        return False   # False = don't suppress exceptions

    async def query(self, sql: str) -> list:
        if self._connection is None:
            raise RuntimeError("Not connected — use 'async with AsyncDatabase(...)'")
        await asyncio.sleep(0.03)  # simulate query round-trip
        self._query_count += 1
        return [{"row": i, "sql": sql} for i in range(3)]


async def demo_class_based():
    print("=" * 60)
    print("PART 1: Class-based async context manager")
    print("=" * 60)
    print()

    # Happy path
    print("  --- Happy path ---")
    async with AsyncDatabase("postgres://lab:secret@localhost/training") as db:
        rows = await db.query("SELECT * FROM users LIMIT 3")
        print(f"    query returned {len(rows)} rows")
        rows2 = await db.query("SELECT * FROM orders LIMIT 5")
        print(f"    second query returned {len(rows2)} rows")
    print("  (after 'async with' block — connection is closed)\n")

    # Exception path — __aexit__ still runs
    print("  --- Exception inside 'async with' ---")
    try:
        async with AsyncDatabase("postgres://lab:secret@localhost/training") as db:
            rows = await db.query("SELECT * FROM users")
            print(f"    first query OK")
            raise ValueError("something went wrong mid-session")
    except ValueError:
        pass
    print("  (connection still closed despite exception)\n")


# ══════════════════════════════════════════════════════════════════════════════
# PART 2: asynccontextmanager decorator (generator style)
#
# Simpler for one-off resources: write it as an async generator.
# yield separates setup (before yield) from teardown (after yield).
# ══════════════════════════════════════════════════════════════════════════════

@asynccontextmanager
async def managed_connection(dsn: str):
    """Generator-style async context manager for a DB connection."""
    print(f"    [setup]    connecting to {dsn}")
    await asyncio.sleep(0.05)
    conn = {"dsn": dsn, "active": True}
    try:
        yield conn                          # context body runs here
    finally:
        print(f"    [teardown] closing {dsn}")
        await asyncio.sleep(0.02)
        conn["active"] = False


async def demo_decorator_style():
    print("=" * 60)
    print("PART 2: @asynccontextmanager decorator style")
    print("=" * 60)
    print()

    async with managed_connection("redis://localhost:6379/0") as conn:
        print(f"    connection active: {conn['active']}")
        await asyncio.sleep(0.02)
        print(f"    using connection for cache lookup")

    print(f"    connection active after 'with': {conn['active']}")
    print()
    print("  Generator style is more concise for simple setup/teardown patterns.")


# ══════════════════════════════════════════════════════════════════════════════
# PART 3: Connection pool pattern
#
# A production pattern: multiple concurrent coroutines sharing a pool.
# Each coroutine acquires a connection, uses it, and releases it back.
# The 'async with pool.acquire() as conn:' idiom is the asyncpg/SQLAlchemy norm.
# ══════════════════════════════════════════════════════════════════════════════

class AsyncConnectionPool:
    """Toy connection pool: a Semaphore limiting concurrent connections."""

    def __init__(self, dsn: str, max_connections: int = 3):
        self.dsn = dsn
        self._sem = asyncio.Semaphore(max_connections)
        self._max = max_connections
        self._created = 0

    @asynccontextmanager
    async def acquire(self):
        async with self._sem:              # blocks if pool is exhausted
            self._created += 1
            conn_id = self._created
            print(f"    [pool] connection {conn_id} acquired  "
                  f"(semaphore: {self._max - self._sem._value}/{self._max} in use)")
            await asyncio.sleep(0.01)     # simulate checkout
            try:
                yield {"id": conn_id, "dsn": self.dsn}
            finally:
                print(f"    [pool] connection {conn_id} released")
                await asyncio.sleep(0.005)  # simulate checkin


async def worker(pool: AsyncConnectionPool, worker_id: int):
    async with pool.acquire() as conn:
        await asyncio.sleep(0.05)         # simulate query work
        return {"worker": worker_id, "conn": conn["id"]}


async def demo_pool():
    print("=" * 60)
    print("PART 3: Connection pool — max 3 connections, 6 concurrent workers")
    print("=" * 60)
    print()

    pool = AsyncConnectionPool("postgres://localhost/training", max_connections=3)
    t0 = time.perf_counter()

    results = await asyncio.gather(*[worker(pool, i) for i in range(6)])

    elapsed = time.perf_counter() - t0
    print()
    for r in results:
        print(f"  worker {r['worker']} used connection {r['conn']}")
    print(f"\n  Total: {elapsed:.3f}s  (6 workers, pool=3, ran in 2 batches × 0.05s)")


async def main():
    await demo_class_based()
    await demo_decorator_style()
    await demo_pool()

    print("\n" + "=" * 60)
    print("KEY POINTS")
    print("=" * 60)
    print()
    print("  __aenter__ / __aexit__ — class-based, full control")
    print("  @asynccontextmanager  — decorator, simpler for small resources")
    print("  Both guarantee cleanup: 'finally' block always runs")
    print("  async with MUST be inside async def — not at module level")
    print()
    print("  Production libraries using this pattern:")
    print("    asyncpg:        async with pool.acquire() as conn:")
    print("    aiohttp:        async with ClientSession() as session:")
    print("    SQLAlchemy:     async with AsyncSession(engine) as session:")


if __name__ == "__main__":
    asyncio.run(main())

"""
11_async_antipatterns.py
=========================
Six async anti-patterns: what fails silently, what crashes, and how to fix it.

Anti-patterns covered:
  1. Forgetting 'await'                  — coroutine never executes
  2. Blocking event loop with time.sleep — all tasks freeze
  3. Blocking with requests.get()        — sync library in async context
  4. Nested asyncio.run()               — RuntimeError
  5. Race condition on shared state      — async is not thread-safe
  6. Swallowing gather() exceptions      — silent failures

Each section: BAD pattern → WHY it fails → GOOD fix

Run:
    python demo/day-06/11_async_antipatterns.py
"""

import asyncio
import time
import warnings


# ══════════════════════════════════════════════════════════════════════════════
# ANTI-PATTERN 1: Forgetting 'await'
#
# BAD:  result = fetch_data()      ← returns a coroutine object, not data
# WHY:  calling an async function without await returns a coroutine object.
#       The function body NEVER runs. Python emits RuntimeWarning but doesn't
#       crash — so this silently does nothing.
# GOOD: result = await fetch_data()
# ══════════════════════════════════════════════════════════════════════════════

async def fetch_data(source: str) -> dict:
    await asyncio.sleep(0.05)
    return {"source": source, "rows": 42}


async def antipattern_1_forgot_await():
    print("=" * 60)
    print("ANTI-PATTERN 1: Forgetting 'await'")
    print("=" * 60)
    print()

    # BAD — coroutine never runs; 'result' is a coroutine object
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        bad_result = fetch_data("users_db")   # no await
        # Python detects unawaited coroutine when it's garbage-collected
        bad_result.close()                    # suppress the secondary warning

    w_msgs = [str(w.message) for w in caught if "coroutine" in str(w.message).lower()]
    print(f"  BAD: fetch_data('users_db') without await:")
    print(f"    type(result) = {type(fetch_data('users_db')).__name__}  ← coroutine object!")
    fetch_data.__name__  # just reference; following line suppresses unused coroutine
    coro = fetch_data("x"); coro.close()  # clean up
    print(f"    value = a coroutine object (body never ran)")
    if w_msgs:
        print(f"    Python warning: {w_msgs[0][:80]}")
    print()

    # GOOD — await it
    good_result = await fetch_data("users_db")
    print(f"  GOOD: result = await fetch_data('users_db')")
    print(f"    type(result) = {type(good_result).__name__}")
    print(f"    value = {good_result}")
    print()
    print("  Symptom: function returns None or a coroutine object instead of data.")
    print("  Fix: always await coroutines; use IDE warnings ('coroutine ... never awaited').")


# ══════════════════════════════════════════════════════════════════════════════
# ANTI-PATTERN 2: time.sleep() blocks the entire event loop
#
# BAD:  time.sleep(n) inside an async function
# WHY:  time.sleep() blocks the OS thread. The event loop runs on one thread,
#       so ALL coroutines are frozen for the sleep duration.
# GOOD: await asyncio.sleep(n) — suspends only the calling coroutine
# ══════════════════════════════════════════════════════════════════════════════

async def blocked_worker(name: str) -> str:
    time.sleep(0.15)           # BAD — blocks event loop
    return f"{name} done"


async def async_worker(name: str) -> str:
    await asyncio.sleep(0.15)  # GOOD — yields to event loop
    return f"{name} done"


async def antipattern_2_blocking_sleep():
    print("\n" + "=" * 60)
    print("ANTI-PATTERN 2: time.sleep() blocks the event loop")
    print("=" * 60)
    print()

    # BAD
    t0 = time.perf_counter()
    bad_results = await asyncio.gather(
        blocked_worker("A"), blocked_worker("B"), blocked_worker("C")
    )
    t_bad = time.perf_counter() - t0
    print(f"  BAD  (time.sleep):      {t_bad:.3f}s  ← 0.15×3=0.45s, no overlap")

    # GOOD
    t0 = time.perf_counter()
    good_results = await asyncio.gather(
        async_worker("A"), async_worker("B"), async_worker("C")
    )
    t_good = time.perf_counter() - t0
    print(f"  GOOD (asyncio.sleep):   {t_good:.3f}s  ← 0.15s, all overlapped")
    print()
    print("  Fix: replace time.sleep() → await asyncio.sleep()")
    print("  For blocking I/O you can't change: use run_in_executor() (see file 09).")


# ══════════════════════════════════════════════════════════════════════════════
# ANTI-PATTERN 3: Synchronous HTTP library in async code
#
# BAD:  using 'requests' (or any synchronous network library) in async code
# WHY:  requests.get() is a BLOCKING call — it freezes the event loop exactly
#       like time.sleep(). All other coroutines stall until the request returns.
# GOOD: use async-native libraries (aiohttp, httpx async client)
#       or run_in_executor() if you cannot switch libraries
#
# We simulate with time.sleep() since we can't import requests in a demo.
# ══════════════════════════════════════════════════════════════════════════════

def sync_http_get(url: str) -> dict:
    """Stand-in for: import requests; requests.get(url).json()"""
    time.sleep(0.15)    # simulates blocking network call
    return {"url": url, "status": 200}


async def bad_async_fetcher(url: str) -> dict:
    result = sync_http_get(url)   # BAD — blocks event loop
    return result


async def good_async_fetcher(url: str) -> dict:
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, sync_http_get, url)   # GOOD
    return result


async def antipattern_3_sync_library():
    print("\n" + "=" * 60)
    print("ANTI-PATTERN 3: Synchronous HTTP library in async code")
    print("=" * 60)
    print()

    urls = ["https://api.example.com/a", "https://api.example.com/b", "https://api.example.com/c"]

    t0 = time.perf_counter()
    bad_results = await asyncio.gather(*[bad_async_fetcher(u) for u in urls])
    t_bad = time.perf_counter() - t0
    print(f"  BAD  (sync lib in async): {t_bad:.3f}s  ← no concurrency")

    t0 = time.perf_counter()
    good_results = await asyncio.gather(*[good_async_fetcher(u) for u in urls])
    t_good = time.perf_counter() - t0
    print(f"  GOOD (run_in_executor):   {t_good:.3f}s  ← concurrent in thread pool")
    print()
    print("  Best fix: switch to async library (aiohttp, httpx).")
    print("  Acceptable fix: run_in_executor to move blocking call off event loop.")


# ══════════════════════════════════════════════════════════════════════════════
# ANTI-PATTERN 4: Nested asyncio.run()
#
# BAD:  calling asyncio.run() inside an already-running event loop
# WHY:  asyncio.run() creates a NEW event loop and tries to make it current.
#       Python 3.10+ raises RuntimeError: "This event loop is already running."
# GOOD: use await (inside async), or asyncio.create_task() to schedule work
# ══════════════════════════════════════════════════════════════════════════════

async def inner_operation() -> str:
    await asyncio.sleep(0.05)
    return "inner result"


async def antipattern_4_nested_run():
    print("\n" + "=" * 60)
    print("ANTI-PATTERN 4: Nested asyncio.run()")
    print("=" * 60)
    print()

    # BAD — calling asyncio.run() from within an async function
    print("  BAD: asyncio.run() inside async def")
    try:
        result = asyncio.run(inner_operation())   # RuntimeError
        print(f"    result: {result}")
    except RuntimeError as e:
        print(f"    RuntimeError: {e}")

    # GOOD — just use await
    print()
    print("  GOOD: use 'await' inside async def")
    result = await inner_operation()
    print(f"    result: {result!r}")
    print()
    print("  Rule: asyncio.run() = top-level entry point only.")
    print("  Inside async context: use await, create_task(), or gather().")


# ══════════════════════════════════════════════════════════════════════════════
# ANTI-PATTERN 5: Race condition on shared state
#
# BAD:  multiple coroutines mutate a shared variable without locking
# WHY:  asyncio is single-threaded but NOT atomic — a coroutine can yield
#       at any 'await' point, and another coroutine can modify shared state
#       between your read and write.
# GOOD: use asyncio.Lock() for simple mutual exclusion
# ══════════════════════════════════════════════════════════════════════════════

async def antipattern_5_race_condition():
    print("\n" + "=" * 60)
    print("ANTI-PATTERN 5: Race condition on shared async state")
    print("=" * 60)
    print()

    # BAD — coroutines yield between reading and writing balance
    balance_bad = 1000
    async def bad_transfer(amount: int, name: str):
        nonlocal balance_bad
        current = balance_bad          # READ
        await asyncio.sleep(0)         # yield — another coroutine can run HERE
        balance_bad = current - amount # WRITE — based on potentially stale READ
        print(f"    {name}: withdrew {amount}, balance now {balance_bad}")

    await asyncio.gather(
        bad_transfer(200, "Alice"),
        bad_transfer(300, "Bob"),
    )
    print(f"  BAD  — expected balance: {1000-200-300}  got: {balance_bad}")
    print(f"  (One withdrawal was overwritten — lost update)")

    # GOOD — asyncio.Lock() ensures only one coroutine modifies balance at a time
    balance_good = 1000
    lock = asyncio.Lock()

    async def good_transfer(amount: int, name: str):
        nonlocal balance_good
        async with lock:
            current = balance_good
            await asyncio.sleep(0)   # safe: lock prevents others from entering
            balance_good = current - amount
        print(f"    {name}: withdrew {amount}, balance now {balance_good}")

    print()
    await asyncio.gather(
        good_transfer(200, "Alice"),
        good_transfer(300, "Bob"),
    )
    print(f"  GOOD — expected balance: {1000-200-300}  got: {balance_good}")
    print()
    print("  Fix: asyncio.Lock() for async mutual exclusion (not threading.Lock!).")


# ══════════════════════════════════════════════════════════════════════════════
# ANTI-PATTERN 6: Swallowing gather() exceptions
#
# BAD:  asyncio.gather() without return_exceptions=True and without proper
#       exception handling — failed tasks can go unnoticed
# WHY:  by default, gather() re-raises the FIRST exception. If you don't
#       handle it, the caller sees an unhandled exception and other tasks'
#       results are lost. With return_exceptions=True but no checks, exceptions
#       silently appear as values in the results list.
# GOOD: always check results for Exception instances when using return_exceptions=True
# ══════════════════════════════════════════════════════════════════════════════

async def sometimes_fails(task_id: int) -> dict:
    await asyncio.sleep(0.05)
    if task_id % 3 == 0:
        raise ValueError(f"task {task_id}: validation error")
    return {"task_id": task_id, "ok": True}


async def antipattern_6_swallowed_exceptions():
    print("\n" + "=" * 60)
    print("ANTI-PATTERN 6: Swallowing gather() exceptions")
    print("=" * 60)
    print()

    # BAD — return_exceptions=True but never check for exceptions
    results = await asyncio.gather(
        *[sometimes_fails(i) for i in range(6)],
        return_exceptions=True,
    )
    exceptions_in_results = sum(1 for r in results if isinstance(r, Exception))
    print("  BAD: return_exceptions=True, never checking:")
    print(f"    'all {len(results)} tasks succeeded'  ← WRONG: {exceptions_in_results} were exceptions")
    print(f"    Proof: {[type(r).__name__ if isinstance(r, Exception) else 'ok' for r in results]}")

    # GOOD — inspect and segregate
    print()
    print("  GOOD: inspect results for Exception instances")
    successes, failures = [], []
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            failures.append((i, r))
            print(f"    task {i}: FAIL → {r}")
        else:
            successes.append(r)
            print(f"    task {i}: OK   → task_id={r['task_id']}")

    print(f"\n  Correctly identified: {len(successes)} successes, {len(failures)} failures")
    print()
    print("  Fix: always iterate results and check isinstance(r, Exception).")


async def main():
    print("6 Async Anti-Patterns — BAD vs GOOD")
    print()
    await antipattern_1_forgot_await()
    await antipattern_2_blocking_sleep()
    await antipattern_3_sync_library()
    await antipattern_4_nested_run()
    await antipattern_5_race_condition()
    await antipattern_6_swallowed_exceptions()

    print("\n" + "=" * 60)
    print("ANTI-PATTERN SUMMARY")
    print("=" * 60)
    print()
    print("  1. Missing await        → coroutine object returned, body skipped")
    print("  2. time.sleep()         → event loop frozen for all coroutines")
    print("  3. sync library         → event loop frozen for all coroutines")
    print("  4. nested asyncio.run() → RuntimeError: this event loop is running")
    print("  5. shared state no lock → lost updates between yield points")
    print("  6. unhandled gather exc → exceptions silently in results list")


if __name__ == "__main__":
    asyncio.run(main())

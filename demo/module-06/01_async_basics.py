"""
01_async_basics.py
===================
async/await fundamentals — from first principles.

Topics:
  1. What a coroutine IS (and isn't) when you call an async function
  2. How asyncio.run() drives the event loop
  3. await suspends the current coroutine, yields control to the event loop
  4. The event loop is single-threaded — one coroutine runs at a time

Key mental model:
  Threads (Module 5):  OS switches between threads pre-emptively
  Async (Module 6):    coroutines cooperate — they yield voluntarily at 'await'

Run:
    python demo/module-06/01_async_basics.py
"""

import asyncio
import time


# ══════════════════════════════════════════════════════════════════════════════
# PART 1: Calling vs awaiting an async function
#
# async def hello() defines a COROUTINE FUNCTION.
# hello()       → returns a coroutine OBJECT  (nothing runs yet)
# await hello() → schedules the coroutine and suspends the caller until done
#
# This is the most common beginner mistake: calling without await and wondering
# why nothing happened. Python will emit a RuntimeWarning in this case.
# ══════════════════════════════════════════════════════════════════════════════

async def hello(name: str) -> str:
    """Simplest async function — suspends for 0s then returns."""
    await asyncio.sleep(0)     # yield to event loop (0-second cooperative yield)
    return f"Hello, {name}!"


async def demo_call_vs_await():
    print("=" * 60)
    print("PART 1: Calling vs awaiting an async function")
    print("=" * 60)
    print()

    # Just calling — returns a coroutine object, does NOT execute the body
    coro = hello("World")
    print(f"  hello('World')  →  {coro}")
    print(f"  type: {type(coro).__name__}")
    print()

    # Must close to avoid 'coroutine was never awaited' warning
    coro.close()

    # Awaiting — drives the coroutine to completion
    result = await hello("World")
    print(f"  await hello('World')  →  {result!r}")
    print()
    print("  Key point: 'await expr' suspends THIS coroutine, gives control")
    print("  to the event loop, and resumes when expr is done.")


# ══════════════════════════════════════════════════════════════════════════════
# PART 2: asyncio.run() — the event loop entry point
#
# asyncio.run(coro) does three things:
#   1. Creates a new event loop
#   2. Runs coro to completion
#   3. Closes the loop and cleans up
#
# It's the bridge between synchronous top-level code and async coroutines.
# You call asyncio.run() ONCE at the program entry point — never nested.
# Nesting it raises: RuntimeError: This event loop is already running.
#
# The live call is at the bottom of this file:
#   asyncio.run(main())     ← this is the ONLY asyncio.run() in the program
#
# Everything below (demo_event_loop, demo_cooperative, …) is already INSIDE
# that event loop, so they use 'await' — not another asyncio.run().
# ══════════════════════════════════════════════════════════════════════════════

async def fetch_data(source: str, delay: float) -> dict:
    """Simulate fetching data from a remote source."""
    await asyncio.sleep(delay)
    return {"source": source, "rows": 42, "delay": delay}


async def demo_event_loop():
    print("\n" + "=" * 60)
    print("PART 2: asyncio.run() and sequential awaits")
    print("=" * 60)
    print()
    print("  asyncio.run(main()) at the bottom of this file:")
    print("    1. Creates a new event loop")
    print("    2. Runs main() to completion")
    print("    3. Closes the loop and cleans up")
    print()
    print("  This function is already INSIDE that loop — it uses 'await',")
    print("  not another asyncio.run() (that would raise RuntimeError).")
    print()

    print("  Sequential fetches — each 'await' suspends this coroutine:")
    t0 = time.perf_counter()

    r1 = await fetch_data("users_db",    delay=0.10)
    r2 = await fetch_data("products_db", delay=0.10)
    r3 = await fetch_data("orders_db",   delay=0.10)

    elapsed = time.perf_counter() - t0
    for r in [r1, r2, r3]:
        print(f"    {r['source']:15s}  rows={r['rows']}  delay={r['delay']}s")
    print(f"\n  Total: {elapsed:.3f}s  ← sequential awaits add up (0.1 × 3 = 0.3s)")
    print()
    print("  Each 'await asyncio.sleep(...)' yields to the event loop — but")
    print("  nothing ELSE is scheduled here, so it just waits in turn.")
    print("  Module 6 file 04 shows how to run all three concurrently.")


# ══════════════════════════════════════════════════════════════════════════════
# PART 3: await pauses here, not everywhere
#
# Demonstrate that await suspends ONLY the current coroutine.
# Other coroutines scheduled with create_task() keep running.
#
# Flow:
#   t=0.00  main creates task_slow (0.3s) and task_fast (0.1s)
#   t=0.00  main awaits asyncio.sleep(0.2)  ← main suspends
#   t=0.10  task_fast completes and prints
#   t=0.20  main's sleep finishes, main resumes and prints
#   t=0.30  task_slow completes and prints
# ══════════════════════════════════════════════════════════════════════════════

async def worker(name: str, delay: float) -> str:
    print(f"    {name}: starting (will take {delay}s)")
    await asyncio.sleep(delay)
    print(f"    {name}: done")
    return f"{name} result"


async def demo_cooperative():
    print("\n" + "=" * 60)
    print("PART 3: Cooperative scheduling — await suspends only THIS coroutine")
    print("=" * 60)
    print()
    print("  Tasks run interleaved on a single thread:")
    print()

    t0 = time.perf_counter()

    # Schedule both tasks — they are now PENDING in the event loop
    task_slow = asyncio.create_task(worker("slow (0.3s)", 0.3))
    task_fast = asyncio.create_task(worker("fast (0.1s)", 0.1))

    # Await main's own sleep — event loop runs other tasks during this time
    await asyncio.sleep(0.2)
    print(f"    main: resumed after 0.2s  (fast task already done)")

    # Collect results
    result_slow = await task_slow
    result_fast = await task_fast

    print()
    print(f"  Total elapsed: {time.perf_counter() - t0:.3f}s  "
          f"(not 0.3+0.3+0.2=0.8s — they overlapped!)")
    print()
    print(f"  Results: {result_fast!r}, {result_slow!r}")


# ══════════════════════════════════════════════════════════════════════════════
# PART 4: async def rules
# ══════════════════════════════════════════════════════════════════════════════

async def demo_rules():
    print("\n" + "=" * 60)
    print("PART 4: The rules of async/await")
    print("=" * 60)
    print()
    print("  1. async def       → defines a coroutine function")
    print("     calling it      → returns a coroutine object (not yet run)")
    print("     await-ing it    → runs it, suspends caller until done")
    print()
    print("  2. await can ONLY appear inside an async def")
    print("     (SyntaxError if you try it at module level or in a plain def)")
    print()
    print("  3. asyncio.run()   → bridges sync → async world")
    print("     Use ONCE at the top level. Never nest asyncio.run() calls.")
    print()
    print("  4. The event loop is SINGLE-THREADED")
    print("     Coroutines take turns. CPU work in a coroutine BLOCKS everything.")
    print("     → For CPU work: use run_in_executor + ProcessPool (see file 09).")
    print()
    print("  5. asyncio.sleep(n) vs time.sleep(n)")
    print("     asyncio.sleep: yields to event loop — other tasks run")
    print("     time.sleep:    BLOCKS the thread — nothing else can run")


async def main():
    await demo_call_vs_await()
    await demo_event_loop()
    await demo_cooperative()
    await demo_rules()


if __name__ == "__main__":
    asyncio.run(main())

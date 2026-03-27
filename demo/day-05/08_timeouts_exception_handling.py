"""
08_timeouts_exception_handling.py
===================================
Production-quality futures: timeouts, exceptions, and partial failures.

Topics:
  1. future.result(timeout=)    — per-future timeout
  2. executor.map(timeout=)     — iterator-level timeout
  3. Collecting exceptions from futures without crashing
  4. Partial success pattern    — process whatever succeeded

Run:
    python demo/day-05/08_timeouts_exception_handling.py
"""

import time
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed


# ══════════════════════════════════════════════════════════════════════════════
# Tasks with varied behaviour — some slow, some raising
# ══════════════════════════════════════════════════════════════════════════════

def unreliable_task(task_id: int) -> dict:
    """
    Simulates an unreliable external API call:
      - task 1 raises ValueError (bad data)
      - task 3 raises ConnectionError (transient failure)
      - task 4 sleeps 2 s (slow / hanging)
      - all others succeed in 0.1 s
    """
    if task_id == 1:
        raise ValueError(f"task {task_id}: bad input data")
    if task_id == 3:
        raise ConnectionError(f"task {task_id}: connection refused")
    if task_id == 4:
        time.sleep(2.0)          # simulates a hung/slow endpoint
    else:
        time.sleep(0.1)
    return {"task_id": task_id, "status": "ok"}


# ══════════════════════════════════════════════════════════════════════════════
# PART 1: Per-future timeout with future.result(timeout=)
#
# future.result(timeout=N) raises concurrent.futures.TimeoutError after N
# seconds if the future has not completed.
#
# The underlying thread keeps running — Python threads cannot be force-killed.
# Use timeouts to enforce SLAs in the caller, not to stop runaway threads.
#
# Flow:
#   - task 4 sleeps 2s, but we call result(timeout=0.5)
#   - After 0.5s the caller receives TimeoutError and continues
#   - Thread is still running in the background (leaks unless daemon=True)
# ══════════════════════════════════════════════════════════════════════════════

def demo_per_future_timeout():
    print("=" * 60)
    print("PART 1: future.result(timeout=0.5s)")
    print("=" * 60)
    print()
    print("  Task 4 sleeps 2s → will exceed 0.5s timeout")
    print()

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(unreliable_task, i): i for i in range(5)}

        for fut, tid in futures.items():
            try:
                result = fut.result(timeout=0.5)
                print(f"  task {tid}: SUCCESS  status={result['status']}")
            except concurrent.futures.TimeoutError:
                print(f"  task {tid}: TIMEOUT  (exceeded 0.5s)")
            except Exception as exc:
                print(f"  task {tid}: ERROR    {type(exc).__name__}: {exc}")

    print()
    print("  The pool context manager waited for running threads before exiting.")
    print("  In production: set executor daemon threads or use explicit shutdown().")


# ══════════════════════════════════════════════════════════════════════════════
# PART 2: map() with timeout=
#
# executor.map(fn, iterable, timeout=N) raises TimeoutError when ITERATING
# results if the NEXT result (in input order) isn't ready within N seconds.
#
# Important: the timeout clock starts when map() is called, not per-result.
# All tasks run in parallel — timeout is measured from the map() call.
# ══════════════════════════════════════════════════════════════════════════════

def fast_task(task_id: int) -> dict:
    """All tasks complete in 0.1s — used to show clean map() behaviour."""
    time.sleep(0.1)
    return {"task_id": task_id, "status": "ok"}


def slow_task(task_id: int) -> dict:
    """Task 2 takes 2s — triggers timeout on iteration."""
    if task_id == 2:
        time.sleep(2.0)
    else:
        time.sleep(0.1)
    return {"task_id": task_id, "status": "ok"}


def demo_map_timeout():
    print("\n" + "=" * 60)
    print("PART 2: executor.map(timeout=0.5s)")
    print("=" * 60)
    print()
    print("  Task 2 sleeps 2s → TimeoutError raised when we reach it in iteration")
    print()

    results_collected = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        result_iter = executor.map(slow_task, range(5), timeout=0.5)
        try:
            for result in result_iter:
                results_collected.append(result)
                print(f"  Got result: task {result['task_id']}")
        except concurrent.futures.TimeoutError:
            print("  TimeoutError raised while iterating — task 2 took too long")

    print(f"\n  Results collected before timeout: {len(results_collected)}")
    print("  (tasks 0,1 finished; task 2 triggered TimeoutError; 3,4 not yielded)")


# ══════════════════════════════════════════════════════════════════════════════
# PART 3: Collecting exceptions with as_completed()
#
# The idiomatic pattern for production code:
#   1. Submit all futures
#   2. Iterate as_completed()
#   3. Call future.result() inside try/except
#   4. Segregate successes and failures
#
# This way a failure in task N doesn't stop tasks 0..N-1 or N+1..M from
# being processed.
# ══════════════════════════════════════════════════════════════════════════════

def demo_partial_success():
    print("\n" + "=" * 60)
    print("PART 3: Partial success — collect exceptions, keep going")
    print("=" * 60)
    print()
    print("  5 tasks: tasks 1 and 3 raise errors, task 4 times out (0.5s limit)")
    print()

    successes = []
    failures  = []

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(unreliable_task, i): i for i in range(5)}

        for fut in as_completed(futures):
            tid = futures[fut]
            try:
                result = fut.result(timeout=0.5)
                successes.append(result)
                print(f"  ✓  task {tid}: {result['status']}")
            except concurrent.futures.TimeoutError:
                failures.append({"task_id": tid, "error": "TimeoutError"})
                print(f"  ✗  task {tid}: TimeoutError")
            except Exception as exc:
                failures.append({"task_id": tid, "error": str(exc)})
                print(f"  ✗  task {tid}: {type(exc).__name__}: {exc}")

    print()
    print(f"  Succeeded: {len(successes)} tasks → {[r['task_id'] for r in successes]}")
    print(f"  Failed:    {len(failures)} tasks → {[f['task_id'] for f in failures]}")
    print()
    print("  All tasks had a chance to complete. Errors collected, not raised.")


def main():
    demo_per_future_timeout()
    demo_map_timeout()
    demo_partial_success()

    print("\n" + "=" * 60)
    print("BEST PRACTICES")
    print("=" * 60)
    print()
    print("  1. Always use future.result(timeout=) in production — never block forever.")
    print("  2. Prefer as_completed() + try/except for partial-success collection.")
    print("  3. map(timeout=) is convenient but all-or-nothing after the timeout.")
    print("  4. Threads can't be killed on timeout — design tasks to be cancellable")
    print("     (check a stop event or use daemon threads that die with the process).")
    print("  5. Log failed task_ids for retry queues, don't silently swallow errors.")


if __name__ == "__main__":
    main()

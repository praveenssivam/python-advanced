"""
06_processpoolexecutor_cpu.py
==============================
ProcessPoolExecutor API — identical to ThreadPoolExecutor, different engine.

Topics:
  1. submit() + Future for CPU tasks
  2. map() for ordered fan-out
  3. as_completed() for completion-order processing
  4. Pickling requirements — why top-level functions are mandatory

Key difference from threads:
  - Each worker is a separate OS process with its own GIL
  - Tasks/results are serialised (pickled) over IPC
  - Start-up cost is higher (~50–200ms for pool creation)

Run:
    python demo/day-05/06_processpoolexecutor_cpu.py
"""

import time
from concurrent.futures import ProcessPoolExecutor, as_completed


# ══════════════════════════════════════════════════════════════════════════════
# Worker functions — MUST be at module top level
#
# When you write: executor.submit(fn, arg)
#   1. Python pickles the function reference (by name) and the argument
#   2. The pickle payload is sent to the worker process via a Pipe/Queue
#   3. Worker unpickles → calls fn(arg) → pickles result → sends back
#
# Lambda, local functions, and methods cannot be pickled.
# Exception: Python 3.12+ allows some closures, but top-level is universal.
# ══════════════════════════════════════════════════════════════════════════════

def cpu_task(task_id: int, n: int = 6_000_000) -> dict:
    """Sum of i² for i in range(n) — CPU-bound, no I/O."""
    t0 = time.perf_counter()
    result = sum(i * i for i in range(n))
    elapsed = time.perf_counter() - t0
    return {"task_id": task_id, "result": result, "elapsed": elapsed}


def cpu_task_variable(args: tuple) -> dict:
    """Variant accepting a tuple (task_id, n) — useful for map() with zip."""
    task_id, n = args
    t0 = time.perf_counter()
    result = sum(i * i for i in range(n))
    elapsed = time.perf_counter() - t0
    return {"task_id": task_id, "result": result, "elapsed": elapsed}


# ══════════════════════════════════════════════════════════════════════════════
# PATTERN A: submit() + Future
#
# Identical API to ThreadPoolExecutor.submit() — swap one class name to change
# from threads → processes.
#
# Flow:
#   t=0.00  executor.submit() × 4   (pool already warmed up)
#   t=0.00  4 OS processes start cpu_task() in parallel
#   t≈0.6s  all finish — future.result() returns
# ══════════════════════════════════════════════════════════════════════════════

def demo_submit():
    print("=" * 60)
    print("PATTERN A: submit() + Future  [ProcessPoolExecutor]")
    print("=" * 60)
    print()

    n_tasks = 4
    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=n_tasks) as executor:
        futures = [executor.submit(cpu_task, i) for i in range(n_tasks)]
        results = [fut.result() for fut in futures]
    t_total = time.perf_counter() - t0

    for r in results:
        print(f"  task {r['task_id']}: {r['elapsed']:.3f}s per-worker time")
    print(f"\n  Wall time (all 4 overlapped): {t_total:.3f}s")
    print(f"  Sum of worker times: {sum(r['elapsed'] for r in results):.3f}s")
    print()
    print("  Wall time ≈ single-task time = true parallel execution.")


# ══════════════════════════════════════════════════════════════════════════════
# PATTERN B: map() — ordered results
#
# Same semantics as ThreadPoolExecutor.map():
#   - Submits all tasks simultaneously
#   - Yields results in INPUT ORDER (blocks on slow tasks)
#   - timeout= parameter raises futures.TimeoutError if a task exceeds it
# ══════════════════════════════════════════════════════════════════════════════

def demo_map():
    print("\n" + "=" * 60)
    print("PATTERN B: map()  [ProcessPoolExecutor]")
    print("=" * 60)
    print()

    n_tasks = 4
    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=n_tasks) as executor:
        results = list(executor.map(cpu_task, range(n_tasks)))
    t_total = time.perf_counter() - t0

    print("  Results in input order:")
    for r in results:
        print(f"    task {r['task_id']}  elapsed={r['elapsed']:.3f}s")
    print(f"\n  Wall time: {t_total:.3f}s")


# ══════════════════════════════════════════════════════════════════════════════
# PATTERN C: as_completed() — completion order
#
# More informative for CPU tasks of unequal length.
# Here we vary n to create tasks of different durations.
# ══════════════════════════════════════════════════════════════════════════════

def demo_as_completed():
    print("\n" + "=" * 60)
    print("PATTERN C: as_completed()  [ProcessPoolExecutor]")
    print("=" * 60)
    print()

    # vary n so tasks finish in a visible order: task3 (n=2M) fastest,
    # task0 (n=8M) slowest
    task_sizes = {0: 8_000_000, 1: 6_000_000, 2: 4_000_000, 3: 2_000_000}
    print("  Task sizes (larger n = longer task):")
    for tid, n in task_sizes.items():
        print(f"    task {tid}: n={n:,}")
    print()

    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(cpu_task, tid, n): tid
            for tid, n in task_sizes.items()
        }
        print("  Completion order (should be task3 first, task0 last):")
        arrival = 0
        for fut in as_completed(futures):
            result = fut.result()
            elapsed = time.perf_counter() - t0
            arrival += 1
            print(f"    #{arrival} at {elapsed:.2f}s — "
                  f"task {result['task_id']} (n={task_sizes[result['task_id']]:,})")

    print()
    print("  Processes with less work finished earlier and were processed immediately.")


# ══════════════════════════════════════════════════════════════════════════════
# PICKLING DEMO — what breaks and why
#
# This section explains (but does NOT execute) what would fail:
#   executor.submit(lambda x: x*x, 5)      → PicklingError: Can't pickle lambdas
#   executor.submit(inner_fn, 5)            → AttributeError: can't find inner_fn
#
# Fix: always define worker functions at module/class (importable) level.
# ══════════════════════════════════════════════════════════════════════════════

def demo_pickling_rules():
    print("\n" + "=" * 60)
    print("PICKLING RULES — ProcessPoolExecutor gotchas")
    print("=" * 60)
    print()
    print("  ✓  Top-level function  → picklable by name reference")
    print("  ✗  Lambda              → PicklingError (no name in module)")
    print("  ✗  Local/inner fn      → AttributeError (not importable)")
    print("  ✓  Top-level callable class (__call__)  → picklable")
    print()
    print("  Arguments must also be picklable:")
    print("  ✓  int, float, str, list, dict, tuple")
    print("  ✗  open file handles, sockets, locks, thread-local state")
    print()
    print("  ProcessPoolExecutor creates a NEW interpreter per worker.")
    print("  Top-level module code is re-imported in each worker — keep")
    print("  module-level side effects (DB connections, file opens) in")
    print("  the worker function itself, not at import time.")


def main():
    print("ProcessPoolExecutor — Three Submission Patterns + Pickling Rules")
    print()
    demo_submit()
    demo_map()
    demo_as_completed()
    demo_pickling_rules()


if __name__ == "__main__":
    main()

"""
05_threadpoolexecutor_basics.py
================================
The three core submission patterns of ThreadPoolExecutor.

Pattern A  submit()      — one future per task, full control
Pattern B  map()         — results in input order, simple fan-out
Pattern C  as_completed() — results in completion order, early processing

All three demonstrated on the same I/O-bound workload (HTTP simulation).

Run:
    python demo/module-05/05_threadpoolexecutor_basics.py
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed


# ══════════════════════════════════════════════════════════════════════════════
# Shared I/O task — same for all three patterns
# ══════════════════════════════════════════════════════════════════════════════

def download(task_id: int, size_kb: int = 100) -> dict:
    """
    Simulate downloading a file (I/O-bound, sleeps proportional to size).
    size_kb=100 → 0.10s latency.
    """
    latency = size_kb / 1000
    time.sleep(latency)
    return {"task_id": task_id, "size_kb": size_kb, "status": "ok"}


# ══════════════════════════════════════════════════════════════════════════════
# PATTERN A: submit() + Future
#
# submit(fn, *args) → Future               (non-blocking, returns immediately)
# future.result()   → return value         (blocks until done, or raises)
# future.done()     → bool                 (non-blocking poll)
# future.cancel()   → bool                 (cancel if not yet started)
#
# Use when you need:
#   - Different tasks with different arguments in one pool
#   - Individual exception handling per task
#   - The ability to cancel specific futures
#
# Flow:
#   t=0.00  submit() × 5  ← all futures handed to thread pool instantly
#   t=0.00  5 threads start running download() in parallel
#   t≈0.10  future.result() returns as each future completes
# ══════════════════════════════════════════════════════════════════════════════

def demo_submit():
    print("=" * 60)
    print("PATTERN A: submit() + Future")
    print("=" * 60)
    print()

    tasks = [(0, 80), (1, 120), (2, 100), (3, 90), (4, 110)]  # (id, size_kb)

    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=5) as executor:
        # submit() returns a Future immediately — work starts in background
        futures = [executor.submit(download, tid, size) for tid, size in tasks]

        # Poll status without blocking (future is already running)
        for i, fut in enumerate(futures):
            print(f"  future[{i}].done() immediately after submit → {fut.done()}")
        print()

        # Block for each result
        results = []
        for fut in futures:
            result = fut.result()   # blocks until this specific future is done
            results.append(result)

    t_total = time.perf_counter() - t0
    print("  Results (in submission order — we iterated futures in order):")
    for r in results:
        print(f"    task {r['task_id']}  size={r['size_kb']}KB  status={r['status']}")
    print(f"\n  Wall time: {t_total:.3f}s  (all tasks overlapped)")


# ══════════════════════════════════════════════════════════════════════════════
# PATTERN B: map()
#
# executor.map(fn, iterable)  → iterator of results in INPUT ORDER
#
# Semantics:
#   - Submits all tasks immediately (same as submit() for each)
#   - Iteration blocks until the NEXT result (in input order) is ready
#   - If task[0] takes 1s and task[1] takes 0.1s, you wait 1s before
#     seeing task[1]'s result, even though it finished in 0.1s.
#
# Use when:
#   - All tasks have the same function signature
#   - You need results in input order
#   - Simple fan-out with no per-task exception handling
# ══════════════════════════════════════════════════════════════════════════════

def demo_map():
    print("\n" + "=" * 60)
    print("PATTERN B: map() — ordered results")
    print("=" * 60)
    print()

    sizes = [100, 100, 100, 100, 100]   # uniform latency to keep output clean

    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=len(sizes)) as executor:
        # map() returns a lazy iterator — no results yet
        result_iter = executor.map(download, range(len(sizes)), sizes)

        # Iterating blocks until the *next result in order* is ready
        results = list(result_iter)

    t_total = time.perf_counter() - t0
    print("  Results (guaranteed input order):")
    for i, r in enumerate(results):
        print(f"    position {i} → task_id={r['task_id']}  status={r['status']}")
    print(f"\n  Wall time: {t_total:.3f}s")
    print()
    print("  Note: map() gives NO gap between results here because all tasks")
    print("  are equal speed. With unequal speeds, order-preserving ordering")
    print("  can make you wait longer than necessary. Use as_completed() then.")


# ══════════════════════════════════════════════════════════════════════════════
# PATTERN C: as_completed()
#
# as_completed(futures)  → iterator that yields futures as they FINISH
#
# Unlike map(), results come in COMPLETION ORDER (fastest first).
# Semantics:
#   - You submit futures beforehand (via submit())
#   - as_completed() blocks until ANY future finishes, yields it
#   - Ideal when you can process each result independently and immediately
#
# Use when:
#   - Tasks have very different latencies (don't wait for slow ones)
#   - You want to display progress as tasks complete
#   - Early results should trigger follow-up work immediately
# ══════════════════════════════════════════════════════════════════════════════

def demo_as_completed():
    print("\n" + "=" * 60)
    print("PATTERN C: as_completed() — completion order")
    print("=" * 60)
    print()

    # Deliberately varied sizes so completion order != submission order
    tasks = [(0, 300), (1, 50), (2, 200), (3, 80), (4, 150)]  # (id, size_kb)
    print("  Submission order: " + ", ".join(f"task {tid}({s}KB)" for tid, s in tasks))
    print("  Expected completion order (fastest first): task1, task3, task4, task2, task0")
    print()

    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(download, tid, size): tid for tid, size in tasks}

        print("  Completion order:")
        arrival = 0
        for fut in as_completed(futures):
            result = fut.result()
            elapsed = time.perf_counter() - t0
            arrival += 1
            print(f"    #{arrival} arrived at {elapsed:.2f}s — "
                  f"task {result['task_id']} ({result['size_kb']}KB)")

    print()
    print("  Results processed immediately on arrival, not waiting for all.")


def main():
    print("ThreadPoolExecutor — Three Submission Patterns")
    print()
    demo_submit()
    demo_map()
    demo_as_completed()

    print("\n" + "=" * 60)
    print("PATTERN COMPARISON")
    print("=" * 60)
    print()
    print("  submit()       → full control, per-future exception handling")
    print("  map()          → simple, input order preserved, same fn/args shape")
    print("  as_completed() → fastest response, completion order, diverse tasks")


if __name__ == "__main__":
    main()

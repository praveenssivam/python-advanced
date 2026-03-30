"""
01_concurrency_fundamentals.py
================================
Concurrency lets a program make progress on multiple tasks at the same time.
Python offers three models — choose the right one for your workload:

  Threading          → multiple threads share one process; good for I/O-bound work
  Multiprocessing    → separate processes with separate memory; good for CPU-bound work
  concurrent.futures → high-level API that wraps both (ThreadPoolExecutor / ProcessPoolExecutor)

This file benchmarks all three on the same simulated I/O task (sleep 0.1 s per request)
so the timing differences are immediately visible.

Run:
    python demo/module-05/01_concurrency_fundamentals.py
"""

import time
import threading
from concurrent.futures import ThreadPoolExecutor


# ══════════════════════════════════════════════════════════════════════════════
# Shared workload — simulate a slow I/O call (network request, DB query, …)
#
# We use time.sleep() to stand in for real I/O.  The sleep releases the GIL,
# which is exactly what real blocking I/O does.  This means threading CAN
# overlap these calls — each thread sleeps independently.
#
# Flow for simulate_request(n):
#   1. Record start time
#   2. sleep(0.1)   ← simulated I/O wait; GIL released here
#   3. Record end time
#   4. Return result string
# ══════════════════════════════════════════════════════════════════════════════

TASK_DURATION = 0.1   # seconds per simulated request
N_REQUESTS    = 5


def simulate_request(request_id: int) -> str:
    """Simulate a single I/O-bound request (e.g. HTTP GET)."""
    time.sleep(TASK_DURATION)
    return f"response-{request_id}"


# ══════════════════════════════════════════════════════════════════════════════
# MODEL 1: Sequential (baseline)
#
# Each request is made one-at-a-time. Total time = N × task_duration.
# ══════════════════════════════════════════════════════════════════════════════

def run_sequential() -> list[str]:
    """Process requests one at a time — the simplest but slowest approach."""
    return [simulate_request(i) for i in range(N_REQUESTS)]


# ══════════════════════════════════════════════════════════════════════════════
# MODEL 2: Threading
#
# Each request runs in its own thread.  Because the task is I/O-bound
# (sleep releases the GIL), threads genuinely overlap.
# Total time ≈ max(individual times) ≈ one task_duration.
#
# Flow:
#   1. Create one Thread per request, all pointing at simulate_request
#   2. Start all threads  → they all begin sleeping simultaneously
#   3. join() waits for every thread to finish
#   4. Results collected from shared list (thread-safe here because each
#      index is written by exactly one thread)
# ══════════════════════════════════════════════════════════════════════════════

def run_threaded() -> list[str]:
    """Process all requests concurrently using threads."""
    results = [None] * N_REQUESTS

    def worker(i):
        results[i] = simulate_request(i)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(N_REQUESTS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    return results


# ══════════════════════════════════════════════════════════════════════════════
# MODEL 3: ThreadPoolExecutor (concurrent.futures)
#
# Higher-level API — manages a pool of threads, submits work as futures,
# collects results.  Functionally equivalent to Model 2 but cleaner.
#
# Flow:
#   1. executor.map(simulate_request, ids) submits all tasks immediately
#   2. Internally uses a thread pool (default workers = min(32, cpu+4))
#   3. map() returns results in input order once all are done
# ══════════════════════════════════════════════════════════════════════════════

def run_with_executor() -> list[str]:
    """Process all requests using ThreadPoolExecutor (high-level API)."""
    with ThreadPoolExecutor(max_workers=N_REQUESTS) as executor:
        return list(executor.map(simulate_request, range(N_REQUESTS)))


# ══════════════════════════════════════════════════════════════════════════════
# Benchmarking harness
# ══════════════════════════════════════════════════════════════════════════════

def benchmark(label: str, fn) -> list[str]:
    t0 = time.perf_counter()
    results = fn()
    elapsed = time.perf_counter() - t0
    speedup = (TASK_DURATION * N_REQUESTS) / elapsed
    print(f"  {label:<35s}  {elapsed:.3f}s   speedup vs sequential: {speedup:.1f}×")
    return results


def main():
    print("=" * 65)
    print("CONCURRENCY FUNDAMENTALS — Three models on I/O-bound work")
    print("=" * 65)
    print(f"\n  Task: {N_REQUESTS} simulated requests × {TASK_DURATION}s each")
    print(f"  Expected sequential total: {N_REQUESTS * TASK_DURATION:.1f}s\n")

    benchmark("1. Sequential (baseline)",            run_sequential)
    benchmark("2. Threading (raw threads)",           run_threaded)
    benchmark("3. ThreadPoolExecutor (futures API)",  run_with_executor)

    print()
    print("  Key insight:")
    print("  ┌─ I/O-bound work → threading gives near-linear speedup")
    print("  │   because sleep() / real I/O releases the GIL.")
    print("  └─ CPU-bound work → threading gives NO speedup (see 02_gil_concept.py)")
    print()
    print("  When to use which model:")
    print("  ┌─ I/O-bound  (network, disk, DB) → ThreadPoolExecutor")
    print("  ├─ CPU-bound  (compute, parsing)  → ProcessPoolExecutor")
    print("  └─ Need async event loop          → asyncio  (Module 6)")


if __name__ == "__main__":
    main()

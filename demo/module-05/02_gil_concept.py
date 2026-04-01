"""
02_gil_concept.py
==================
The Global Interpreter Lock (GIL) is a mutex that allows only ONE Python
thread to execute bytecode at a time in CPython.

Consequence:
  CPU-bound work  → threads cannot run truly in parallel (GIL held)
  I/O-bound work  → threads CAN overlap (GIL released during I/O / sleep)
  Multiprocessing → each process has its OWN GIL → true CPU parallelism

This file demonstrates all three scenarios with measurable timings.

Run:
    python demo/module-05/02_gil_concept.py
"""

import time
import threading
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor


# ══════════════════════════════════════════════════════════════════════════════
# PART 1: CPU-bound with threading — GIL prevents parallelism
#
# Both threads want to execute Python bytecode simultaneously.
# The GIL serialises them — you pay thread overhead on top of sequential cost.
#
# Flow for two-thread CPU test:
#   thread-A starts: acquires GIL, computes for a while, releases GIL
#   thread-B starts: acquires GIL (had to wait), computes, …
#   Wall time ≈ sequential time + scheduling overhead  (NOT halved)
# ══════════════════════════════════════════════════════════════════════════════

def cpu_task(n: int = 5_000_000) -> int:
    """Pure CPU work — no I/O, no sleep. GIL is held continuously."""
    return sum(i * i for i in range(n))


def run_cpu_sequential(n_tasks: int = 2) -> float:
    t0 = time.perf_counter()
    for _ in range(n_tasks):
        cpu_task()
    return time.perf_counter() - t0


def run_cpu_threaded(n_tasks: int = 2) -> float:
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=n_tasks) as ex:
        list(ex.map(lambda _: cpu_task(), range(n_tasks)))
    return time.perf_counter() - t0


def demo_cpu_threading():
    print("=" * 60)
    print("PART 1: CPU-bound work with threading")
    print("=" * 60)
    print()
    print("  Running sum(i² for i in range(5M)) × 2 tasks …")
    print()

    t_seq = run_cpu_sequential()
    t_thr = run_cpu_threaded()

    print(f"  Sequential (2 tasks, 1 thread):  {t_seq:.2f}s")
    print(f"  Threaded   (2 tasks, 2 threads): {t_thr:.2f}s")
    ratio = t_thr / t_seq
    print(f"  Ratio (threaded / sequential):   {ratio:.2f}×")
    print()
    print("  Expected: ratio ≈ 1.0 or worse (GIL prevents true parallelism).")
    print("  Threading overhead may even make it SLOWER.")


# ══════════════════════════════════════════════════════════════════════════════
# PART 2: I/O-bound with threading — GIL released, overlap occurs
#
# time.sleep() releases the GIL for the duration of the sleep.
# While thread-A sleeps, thread-B can acquire the GIL and do work.
# All threads sleep simultaneously → wall time ≈ one sleep duration.
#
# Flow:
#   t=0.00  thread-A starts sleep(0.1)  → releases GIL
#           thread-B starts sleep(0.1)  → runs immediately (GIL available)
#           thread-C starts sleep(0.1)  → runs immediately
#   t=0.10  all three wake up, total elapsed ≈ 0.1s
# ══════════════════════════════════════════════════════════════════════════════

SLEEP_DURATION = 0.1


def io_task(task_id: int) -> str:
    """Simulated I/O. sleep() releases the GIL — pure-I/O equivalent."""
    time.sleep(SLEEP_DURATION)
    return f"result-{task_id}"


def run_io_sequential(n: int = 3) -> float:
    t0 = time.perf_counter()
    [io_task(i) for i in range(n)]
    return time.perf_counter() - t0


def run_io_threaded(n: int = 3) -> float:
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=n) as ex:
        list(ex.map(io_task, range(n)))
    return time.perf_counter() - t0


def demo_io_threading():
    print("\n" + "=" * 60)
    print("PART 2: I/O-bound work with threading")
    print("=" * 60)
    print()
    n = 3
    print(f"  Running {n} I/O tasks × {SLEEP_DURATION}s each …")
    print()

    t_seq = run_io_sequential(n)
    t_thr = run_io_threaded(n)
    speedup = t_seq / t_thr

    print(f"  Sequential ({n} tasks, 1 thread):  {t_seq:.2f}s")
    print(f"  Threaded   ({n} tasks, {n} threads): {t_thr:.2f}s")
    print(f"  Speedup:                           {speedup:.1f}×")
    print()
    print(f"  Expected: speedup ≈ {n}× (tasks overlap because GIL is released).")


# ══════════════════════════════════════════════════════════════════════════════
# PART 3: CPU-bound with multiprocessing — true parallelism
#
# Each Process has its OWN Python interpreter and its OWN GIL.
# Two processes can execute Python bytecode simultaneously on separate cores.
# Overhead: spawning processes + IPC serialisation.  Worth it for heavy CPU work.
#
# IMPORTANT: multiprocessing workers must be importable top-level functions
# (no lambdas, no inner functions) because they are pickled and sent to the
# worker process.  cpu_task() is defined at module level so it pickles fine.
# ══════════════════════════════════════════════════════════════════════════════

def run_cpu_multiprocessing(n_tasks: int = 2) -> float:
    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=n_tasks) as ex:
        list(ex.map(cpu_task, [5_000_000] * n_tasks))
    return time.perf_counter() - t0


def demo_cpu_multiprocessing():
    print("\n" + "=" * 60)
    print("PART 3: CPU-bound work with multiprocessing")
    print("=" * 60)
    print()
    print("  Running the same CPU task with ProcessPoolExecutor …")
    print()

    t_seq = run_cpu_sequential()
    t_mp  = run_cpu_multiprocessing()
    speedup = t_seq / t_mp

    print(f"  Sequential (2 tasks, 1 process):   {t_seq:.2f}s")
    print(f"  Multiproc  (2 tasks, 2 processes): {t_mp:.2f}s")
    print(f"  Speedup:                           {speedup:.1f}×")
    print()
    print("  Expected: speedup ≈ 2× (limited by available cores and process overhead).")


# ══════════════════════════════════════════════════════════════════════════════
# Summary
# ══════════════════════════════════════════════════════════════════════════════

def print_summary():
    print("\n" + "=" * 60)
    print("GIL DECISION GUIDE")
    print("=" * 60)
    print("""
  Scenario                  │ Best tool            │ Why
  ──────────────────────────┼──────────────────────┼────────────────────────
  I/O-bound (network, disk) │ ThreadPoolExecutor   │ GIL released during I/O
  CPU-bound (compute)       │ ProcessPoolExecutor  │ Each process has own GIL
  CPU-bound but simple      │ Single thread        │ Process overhead > gain
  Mix of both               │ asyncio (Module 6)      │ Cooperative scheduling
""")


def main():
    demo_cpu_threading()
    demo_io_threading()
    demo_cpu_multiprocessing()
    print_summary()


if __name__ == "__main__":
    main()

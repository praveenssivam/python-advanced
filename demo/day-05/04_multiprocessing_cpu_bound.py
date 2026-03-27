"""
04_multiprocessing_cpu_bound.py
================================
ProcessPoolExecutor bypasses the GIL for true CPU parallelism.

Topics:
  1. Sequential baseline — 4 heavy tasks run one after another
  2. ProcessPoolExecutor — 4 tasks run in 4 separate processes (own GIL each)
  3. Process spawn overhead — why small tasks don't benefit
  4. Chunking — how to amortise overhead for many small tasks

Important: worker functions MUST be defined at module top level.
           They are serialised (pickled) and sent to worker processes.

Run:
    python demo/day-05/04_multiprocessing_cpu_bound.py
"""

import time
from concurrent.futures import ProcessPoolExecutor


# ══════════════════════════════════════════════════════════════════════════════
# Worker — must be at module top level for pickling
#
# Pickling is how Python sends a function to a worker process:
#   1. Parent serialises (pickles) the function name + arguments
#   2. Worker process deserialises and calls the function
#   3. Result is pickled back
#
# Lambda, local, and nested functions cannot be pickled → use top-level only.
# ══════════════════════════════════════════════════════════════════════════════

def heavy_compute(task_id: int, n: int = 8_000_000) -> dict:
    """CPU-intensive work: sum of squares up to n."""
    t0 = time.perf_counter()
    result = sum(i * i for i in range(n))
    elapsed = time.perf_counter() - t0
    return {"task_id": task_id, "result": result, "elapsed": elapsed}


def tiny_compute(task_id: int, n: int = 10_000) -> dict:
    """Tiny CPU task — too small to benefit from process overhead."""
    t0 = time.perf_counter()
    result = sum(i * i for i in range(n))
    elapsed = time.perf_counter() - t0
    return {"task_id": task_id, "result": result, "elapsed": elapsed}


# ══════════════════════════════════════════════════════════════════════════════
# PART 1: Sequential baseline
#
# Flow:
#   task 0 starts → finishes (~0.5s) → task 1 starts → … → task 3 finishes
#   Total ≈ 4 × 0.5s = 2.0s
# ══════════════════════════════════════════════════════════════════════════════

def demo_sequential():
    print("=" * 60)
    print("PART 1: Sequential baseline (4 heavy tasks)")
    print("=" * 60)
    print()

    t0 = time.perf_counter()
    results = [heavy_compute(i) for i in range(4)]
    t_total = time.perf_counter() - t0

    for r in results:
        print(f"  task {r['task_id']}: elapsed {r['elapsed']:.3f}s")
    print(f"\n  Total: {t_total:.3f}s")
    return t_total


# ══════════════════════════════════════════════════════════════════════════════
# PART 2: ProcessPoolExecutor — 4 workers, true parallelism
#
# Flow:
#   t=0.00  executor.map() submits all 4 tasks
#   t=0.00  4 worker processes spawn (each with its own Python interpreter + GIL)
#   t=0.00  all 4 processes compute simultaneously on separate CPU cores
#   t≈0.5s  all 4 finish — total wall time ≈ single-task time + spawn overhead
#
# max_workers=4 → 4 processes. On a 2-core machine, 2 run at a time;
# on a 4-core machine, all 4 run in parallel.
# ══════════════════════════════════════════════════════════════════════════════

def demo_multiprocessing():
    print("\n" + "=" * 60)
    print("PART 2: ProcessPoolExecutor (4 workers)")
    print("=" * 60)
    print()

    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(heavy_compute, range(4)))
    t_total = time.perf_counter() - t0

    for r in results:
        print(f"  task {r['task_id']}: elapsed {r['elapsed']:.3f}s")
    print(f"\n  Total: {t_total:.3f}s")
    return t_total


# ══════════════════════════════════════════════════════════════════════════════
# PART 3: Process spawn overhead
#
# Starting a process takes ~50–150ms (fork/spawn + import Python + unpickle).
# For tasks shorter than that overhead, multiprocessing makes things SLOWER.
#
# Rule of thumb: use ProcessPoolExecutor only when each task takes > 0.2s.
# For many tiny tasks: chunk them (pass a batch per worker).
# ══════════════════════════════════════════════════════════════════════════════

def demo_spawn_overhead():
    print("\n" + "=" * 60)
    print("PART 3: Spawn overhead — tiny tasks get slower, not faster")
    print("=" * 60)
    print()

    n_tasks = 20

    t0 = time.perf_counter()
    seq_results = [tiny_compute(i) for i in range(n_tasks)]
    t_seq = time.perf_counter() - t0

    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=4) as executor:
        mp_results = list(executor.map(tiny_compute, range(n_tasks)))
    t_mp = time.perf_counter() - t0

    print(f"  {n_tasks} tiny tasks (n=10_000 each)")
    print(f"  Sequential:        {t_seq:.3f}s")
    print(f"  ProcessPoolExec:   {t_mp:.3f}s  ← likely SLOWER due to spawn overhead")
    print()
    print("  Why: each task ~0.0001s, but process spawn ~0.05-0.15s.")
    print("  Overhead dominates when task_time << spawn_time.")
    print()
    print("  Fix: chunk tasks so each worker does more work per round-trip.")
    print("  For tiny CPU tasks stay sequential or use numpy/C extensions.")


def main():
    t_seq = demo_sequential()
    t_mp = demo_multiprocessing()
    speedup = t_seq / t_mp
    print(f"\n  Speedup: {speedup:.1f}×  (theoretical max = number of CPU cores)")
    print("  Actual speedup depends on CPU count and spawn overhead.")
    print()

    demo_spawn_overhead()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print()
    print("  ProcessPoolExecutor:")
    print("    ✓  Bypasses the GIL — true CPU parallelism")
    print("    ✓  Simple API — same as ThreadPoolExecutor")
    print("    ✗  Spawn overhead ~50-150ms per executor creation")
    print("    ✗  Workers communicate via pickle — data must be serialisable")
    print("    ✗  No shared memory (each process is isolated)")
    print()
    print("  Use when: CPU-bound, each task > 0.2s, data fits in RAM twice")


if __name__ == "__main__":
    main()

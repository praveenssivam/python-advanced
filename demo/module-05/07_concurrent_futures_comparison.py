"""
07_concurrent_futures_comparison.py
=====================================
Head-to-head benchmark: ThreadPoolExecutor vs ProcessPoolExecutor
on the same I/O-bound and CPU-bound workloads.

Core lesson:
  I/O-bound  → ThreadPool wins    (GIL released during I/O, no spawn cost)
  CPU-bound  → ProcessPool wins   (bypasses GIL, true parallelism)

Run:
    python demo/module-05/07_concurrent_futures_comparison.py
"""

import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor


N_WORKERS = 4


# ══════════════════════════════════════════════════════════════════════════════
# Worker functions — top level (process pool requires pickling)
# ══════════════════════════════════════════════════════════════════════════════

def io_task(task_id: int) -> dict:
    """Simulate I/O: sleep 0.2s (GIL released for threads)."""
    time.sleep(0.2)
    return {"task_id": task_id, "type": "io"}


def cpu_task(task_id: int) -> dict:
    """CPU-intensive: sum of squares (GIL held for threads)."""
    result = sum(i * i for i in range(5_000_000))
    return {"task_id": task_id, "type": "cpu", "result": result}


# ══════════════════════════════════════════════════════════════════════════════
# Generic benchmark runner
# ══════════════════════════════════════════════════════════════════════════════

def run_benchmark(label: str, executor_cls, task_fn, n_tasks: int) -> float:
    """Run n_tasks using executor_cls and return wall time."""
    t0 = time.perf_counter()
    with executor_cls(max_workers=N_WORKERS) as executor:
        list(executor.map(task_fn, range(n_tasks)))
    return time.perf_counter() - t0


def run_sequential(task_fn, n_tasks: int) -> float:
    """Sequential baseline."""
    t0 = time.perf_counter()
    [task_fn(i) for i in range(n_tasks)]
    return time.perf_counter() - t0


# ══════════════════════════════════════════════════════════════════════════════
# EXPERIMENT 1: I/O-bound
#
# Expected results:
#   Sequential     ≈ 4 × 0.2 = 0.80s
#   ThreadPool     ≈ 0.20s          ← threads overlap I/O (GIL released)
#   ProcessPool    ≈ 0.20–0.50s     ← also overlaps, but spawn cost added
#
# ThreadPool advantage: no process spawn overhead (threads reuse the process).
# ProcessPool is correct but wasteful — you paid process overhead for no gain.
# ══════════════════════════════════════════════════════════════════════════════

def demo_io_bound():
    n_tasks = 4
    print("=" * 60)
    print(f"EXPERIMENT 1: I/O-bound  ({n_tasks} tasks × 0.2s sleep)")
    print("=" * 60)
    print()

    t_seq = run_sequential(io_task, n_tasks)
    t_thread = run_benchmark("thread", ThreadPoolExecutor, io_task, n_tasks)
    t_proc = run_benchmark("process", ProcessPoolExecutor, io_task, n_tasks)

    print(f"  Sequential:       {t_seq:.3f}s   (baseline)")
    print(f"  ThreadPoolExec:   {t_thread:.3f}s   speedup={t_seq/t_thread:.1f}×  ← winner")
    print(f"  ProcessPoolExec:  {t_proc:.3f}s   speedup={t_seq/t_proc:.1f}×  (spawn overhead)")
    print()
    print("  Why threads win: GIL is released during time.sleep(), so threads")
    print("  overlap I/O perfectly. Processes also parallelise but the spawn")
    print("  and pickle cost makes them more expensive for short I/O tasks.")


# ══════════════════════════════════════════════════════════════════════════════
# EXPERIMENT 2: CPU-bound
#
# Expected results:
#   Sequential     ≈ 4 × 0.3 = 1.20s
#   ThreadPool     ≈ 1.20s          ← GIL prevents true parallelism
#   ProcessPool    ≈ 0.30–0.40s     ← 4 processes, each with own GIL
#
# ThreadPool looks like it runs in parallel but the GIL forces threads to
# take turns on the Python bytecode interpreter. Net effect: same as sequential.
# ══════════════════════════════════════════════════════════════════════════════

def demo_cpu_bound():
    n_tasks = 4
    print("\n" + "=" * 60)
    print(f"EXPERIMENT 2: CPU-bound  ({n_tasks} tasks, n=5M each)")
    print("=" * 60)
    print()

    t_seq = run_sequential(cpu_task, n_tasks)
    t_thread = run_benchmark("thread", ThreadPoolExecutor, cpu_task, n_tasks)
    t_proc = run_benchmark("process", ProcessPoolExecutor, cpu_task, n_tasks)

    print(f"  Sequential:       {t_seq:.3f}s   (baseline)")
    print(f"  ThreadPoolExec:   {t_thread:.3f}s   speedup={t_seq/t_thread:.1f}×  (GIL bottleneck)")
    print(f"  ProcessPoolExec:  {t_proc:.3f}s   speedup={t_seq/t_proc:.1f}×  ← winner")
    print()
    print("  Why threads lose: the GIL serialises Python bytecode execution.")
    print("  Even with 4 threads, only 1 runs Python at a time.")
    print("  Processes bypass this — each subprocess has its own GIL.")


# ══════════════════════════════════════════════════════════════════════════════
# DECISION TABLE
# ══════════════════════════════════════════════════════════════════════════════

def print_decision_table():
    print("\n" + "=" * 60)
    print("DECISION TABLE")
    print("=" * 60)
    print()
    print("  Workload type         ThreadPool    ProcessPool    asyncio")
    print("  ─────────────────     ──────────    ───────────    ───────")
    print("  Network I/O           ✓ Good        ~ Overkill     ✓ Best")
    print("  File I/O              ✓ Good        ~ Overkill     ✓ Good")
    print("  CPU computation       ✗ GIL lock    ✓ Best         ✗ No help")
    print("  Mixed CPU + I/O       ~ Partial     ✓ Safer        ~ Depends")
    print()
    print("  Overhead")
    print("  ─────────────────     ──────────    ───────────    ───────")
    print("  Startup cost          Very low      Medium (+100ms) Very low")
    print("  Memory per worker     ~1 MB          ~30–80 MB      ~0 MB")
    print("  Shared state          Yes (careful)  No (IPC only)  Yes (easy)")
    print()
    print("  Rule of thumb:")
    print("    I/O-bound → ThreadPoolExecutor")
    print("    CPU-bound → ProcessPoolExecutor")
    print("    Async I/O at scale → asyncio (Module 6)")


def main():
    print("ThreadPoolExecutor vs ProcessPoolExecutor — Head-to-Head")
    print()
    demo_io_bound()
    demo_cpu_bound()
    print_decision_table()


if __name__ == "__main__":
    main()

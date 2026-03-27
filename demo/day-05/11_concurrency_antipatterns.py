"""
11_concurrency_antipatterns.py
================================
Five concurrency anti-patterns: what goes wrong and how to fix it.

Anti-patterns covered:
  1. Threading for CPU-bound work  → GIL bottleneck (use ProcessPool)
  2. Race condition                → unprotected shared state (use Lock)
  3. Silent exception swallowing   → futures.result() never called (always retrieve)
  4. Executor starvation           → max_workers too low for I/O tasks (size correctly)
  5. Lock ordering violation       → deadlock from inconsistent lock order (use hierarchy)

Each section shows:
  BAD  — the problematic pattern
  WHY  — explanation of the failure
  GOOD — the corrected version

Run:
    python demo/day-05/11_concurrency_antipatterns.py
"""

import time
import threading
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor


# ══════════════════════════════════════════════════════════════════════════════
# TOP-LEVEL worker (required for ProcessPoolExecutor pickling)
# ══════════════════════════════════════════════════════════════════════════════

def cpu_work(n: int = 3_000_000) -> int:
    return sum(i * i for i in range(n))


# ══════════════════════════════════════════════════════════════════════════════
# ANTI-PATTERN 1: Threading for CPU-bound work
#
# BAD:  using ThreadPoolExecutor for pure Python computation
# WHY:  the GIL prevents threads from running Python bytecodes in parallel
#       — you pay thread overhead but get no speedup
# GOOD: use ProcessPoolExecutor for CPU-bound tasks
# ══════════════════════════════════════════════════════════════════════════════

def antipattern_1_cpu_threading():
    print("=" * 60)
    print("ANTI-PATTERN 1: Threading for CPU-bound work")
    print("=" * 60)
    print()

    n_tasks = 4

    # BAD
    t0 = time.perf_counter()
    seq_result = [cpu_work() for _ in range(n_tasks)]
    t_seq = time.perf_counter() - t0

    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=n_tasks) as ex:
        bad_results = list(ex.map(cpu_work, [3_000_000] * n_tasks))
    t_thread = time.perf_counter() - t0

    # GOOD
    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=n_tasks) as ex:
        good_results = list(ex.map(cpu_work, [3_000_000] * n_tasks))
    t_proc = time.perf_counter() - t0

    print(f"  Sequential:        {t_seq:.2f}s")
    print(f"  BAD  (ThreadPool): {t_thread:.2f}s  speedup={t_seq/t_thread:.1f}×  "
          f"← GIL prevents overlap")
    print(f"  GOOD (ProcPool):   {t_proc:.2f}s  speedup={t_seq/t_proc:.1f}×  "
          f"← true parallelism")
    print()
    print("  Fix: swap ThreadPoolExecutor → ProcessPoolExecutor for CPU tasks.")


# ══════════════════════════════════════════════════════════════════════════════
# ANTI-PATTERN 2: Race condition — unprotected shared counter
#
# BAD:  two threads increment counter without synchronisation
# WHY:  LOAD/ADD/STORE is not atomic — interleaved execution loses updates
# GOOD: use threading.Lock around the increment
# ══════════════════════════════════════════════════════════════════════════════

def antipattern_2_race_condition():
    print("\n" + "=" * 60)
    print("ANTI-PATTERN 2: Race condition — unprotected shared state")
    print("=" * 60)
    print()

    n = 500_000
    expected = n * 2

    # BAD
    bad_counter = 0
    def bad_increment():
        nonlocal bad_counter
        for _ in range(n):
            bad_counter += 1    # not atomic

    t1, t2 = threading.Thread(target=bad_increment), threading.Thread(target=bad_increment)
    t1.start(); t2.start()
    t1.join();  t2.join()

    # GOOD
    good_counter = 0
    lock = threading.Lock()
    def good_increment():
        nonlocal good_counter
        for _ in range(n):
            with lock:
                good_counter += 1

    t1, t2 = threading.Thread(target=good_increment), threading.Thread(target=good_increment)
    t1.start(); t2.start()
    t1.join();  t2.join()

    print(f"  Expected:      {expected:,}")
    print(f"  BAD  (no lock): {bad_counter:,}  "
          f"← lost {expected - bad_counter:,} increments")
    print(f"  GOOD (lock):   {good_counter:,}  correct={good_counter == expected}")
    print()
    print("  Fix: wrap all read-modify-write operations in 'with lock:'.")


# ══════════════════════════════════════════════════════════════════════════════
# ANTI-PATTERN 3: Silent exception swallowing
#
# BAD:  submitting futures but never calling future.result()
# WHY:  exceptions in worker threads are stored in the Future, not re-raised
#       automatically — they silently disappear if result() is never called
# GOOD: always retrieve results (or explicitly check future.exception())
# ══════════════════════════════════════════════════════════════════════════════

def antipattern_3_silent_exceptions():
    print("\n" + "=" * 60)
    print("ANTI-PATTERN 3: Silent exception swallowing")
    print("=" * 60)
    print()

    def failing_task(task_id: int) -> dict:
        if task_id % 2 == 0:
            raise ValueError(f"task {task_id} failed!")
        return {"task_id": task_id, "ok": True}

    # BAD — submit and discard futures
    print("  BAD: submitting futures and ignoring them")
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(failing_task, i) for i in range(4)]
        # futures go out of scope here — exceptions never surfaced
    print("  (pool exited cleanly — no errors visible even though 2 tasks failed!)")
    print()

    # GOOD — always call result()
    print("  GOOD: always call future.result() or future.exception()")
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(failing_task, i) for i in range(4)]
        for i, fut in enumerate(futures):
            exc = fut.exception()
            if exc:
                print(f"  task {i}: ERROR → {exc}")
            else:
                print(f"  task {i}: OK    → {fut.result()}")

    print()
    print("  Fix: always iterate futures and call .result() or .exception().")
    print("  Prefer as_completed() + try/except for production code.")


# ══════════════════════════════════════════════════════════════════════════════
# ANTI-PATTERN 4: Executor starvation — max_workers too small
#
# BAD:  ThreadPoolExecutor with 2 workers for 10 I/O tasks of 0.1s each
# WHY:  with 2 workers, tasks queue up — total time = ceil(10/2) × 0.1 = 0.5s
#       instead of 0.1s with 10 workers
# GOOD: set max_workers to match the I/O concurrency you need
#       (thread memory is cheap; 50–100 threads for I/O is fine)
# ══════════════════════════════════════════════════════════════════════════════

def antipattern_4_starvation():
    print("\n" + "=" * 60)
    print("ANTI-PATTERN 4: Executor starvation — max_workers too low")
    print("=" * 60)
    print()

    def io_work(_: int) -> str:
        time.sleep(0.1)
        return "ok"

    n = 10

    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=2) as ex:    # BAD: only 2 workers
        list(ex.map(io_work, range(n)))
    t_bad = time.perf_counter() - t0

    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=n) as ex:    # GOOD: one worker per task
        list(ex.map(io_work, range(n)))
    t_good = time.perf_counter() - t0

    print(f"  {n} I/O tasks × 0.1s each:")
    print(f"  BAD  (2 workers):  {t_bad:.2f}s  ← tasks queue up, 5 batches")
    print(f"  GOOD ({n} workers): {t_good:.2f}s  ← all run simultaneously")
    print()
    print("  Guideline for I/O-bound:")
    print("    max_workers = min(32, os.cpu_count() + 4)  # Python 3.8+ default")
    print("  or measure empirically: max_workers ≈ (task_duration / overhead)")


# ══════════════════════════════════════════════════════════════════════════════
# ANTI-PATTERN 5: Deadlock from inconsistent lock ordering
#
# BAD:  Thread A acquires lock_x then lock_y
#       Thread B acquires lock_y then lock_x
#       Both wait for the other → DEADLOCK
# WHY:  circular wait — each thread holds a resource the other needs
# GOOD: define a global lock ordering (always acquire x before y)
#       Both threads follow the SAME order → no circular wait possible
#
# NOTE: We demonstrate deadlock detection by using acquire(timeout=),
#       not an actual hang. Hanging the demo process is not useful in a class.
# ══════════════════════════════════════════════════════════════════════════════

def antipattern_5_deadlock():
    print("\n" + "=" * 60)
    print("ANTI-PATTERN 5: Deadlock from inconsistent lock ordering")
    print("=" * 60)
    print()

    lock_x = threading.Lock()
    lock_y = threading.Lock()
    deadlock_detected = threading.Event()

    def thread_a():
        lock_x.acquire()
        time.sleep(0.05)           # let thread-B grab lock_y first
        if not lock_y.acquire(timeout=0.2):
            deadlock_detected.set()
        else:
            lock_y.release()
        lock_x.release()

    def thread_b():
        lock_y.acquire()
        time.sleep(0.05)           # let thread-A grab lock_x first
        if not lock_x.acquire(timeout=0.2):
            deadlock_detected.set()
        else:
            lock_x.release()
        lock_y.release()

    ta = threading.Thread(target=thread_a)
    tb = threading.Thread(target=thread_b)
    ta.start(); tb.start()
    ta.join();  tb.join()

    print(f"  BAD  (inconsistent order: A=x→y, B=y→x)")
    print(f"  Deadlock detected: {deadlock_detected.is_set()}")
    print()

    # GOOD: both threads always acquire x before y
    def safe_thread_a():
        with lock_x:
            with lock_y:           # consistent order: x then y
                time.sleep(0.02)

    def safe_thread_b():
        with lock_x:               # SAME order as A: x then y
            with lock_y:
                time.sleep(0.02)

    t0 = time.perf_counter()
    ta = threading.Thread(target=safe_thread_a)
    tb = threading.Thread(target=safe_thread_b)
    ta.start(); tb.start()
    ta.join();  tb.join()
    elapsed = time.perf_counter() - t0

    print(f"  GOOD (consistent order: both x→y)")
    print(f"  Completed in {elapsed:.3f}s — no deadlock")
    print()
    print("  Rule: if you ever hold multiple locks, ALWAYS acquire them in the")
    print("  same global order everywhere in the codebase.")
    print("  Alternative: use threading.RLock or higher-level Queue/asyncio.")


def main():
    print("5 Concurrency Anti-Patterns — BAD vs GOOD")
    print()
    antipattern_1_cpu_threading()
    antipattern_2_race_condition()
    antipattern_3_silent_exceptions()
    antipattern_4_starvation()
    antipattern_5_deadlock()

    print("\n" + "=" * 60)
    print("ANTI-PATTERN SUMMARY")
    print("=" * 60)
    print()
    print("  1. Threading CPU  → use ProcessPoolExecutor instead")
    print("  2. Race condition → Lock all shared read-modify-write")
    print("  3. Silent errors  → always call future.result() or .exception()")
    print("  4. Starvation     → size max_workers to match I/O concurrency")
    print("  5. Deadlock       → enforce consistent global lock ordering")


if __name__ == "__main__":
    main()

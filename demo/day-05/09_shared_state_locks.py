"""
09_shared_state_locks.py
=========================
Race conditions and threading.Lock — hands-on demonstration.

This file proves empirically that:
  1. Incrementing a counter from two threads WITHOUT a lock loses updates.
  2. The SAME increment WITH a lock is always correct.

Theory recap:
  counter += 1   compiles to three bytecode ops:
    LOAD_FAST   counter
    LOAD_CONST  1
    BINARY_ADD
    STORE_FAST  counter

  The GIL can be released between any two bytecodes.  If thread-B runs its
  LOAD_FAST before thread-A's STORE_FAST, both threads add to the OLD value
  and one increment is silently lost.

Run:
    python demo/day-05/09_shared_state_locks.py
"""

import threading
import time


# ══════════════════════════════════════════════════════════════════════════════
# PART 1: Unsafe counter — race condition
#
# Two threads each do N increments.
# Expected total: 2 × N.
# Actual total (without lock): significantly less than 2 × N.
#
# Timeline (simplified, one lost increment):
#
#   Thread-A             Thread-B
#   ────────             ────────
#   LOAD  counter=1000
#                        LOAD  counter=1000   ← B reads same stale value
#   ADD   → 1001
#   STORE counter=1001
#                        ADD   → 1001
#                        STORE counter=1001   ← B overwrites A's store
#
# Net effect: two increments happened, counter only moved from 1000 → 1001.
# One increment was LOST.
# ══════════════════════════════════════════════════════════════════════════════

class UnsafeCounter:
    def __init__(self):
        self.value = 0

    def increment(self, n: int) -> None:
        for _ in range(n):
            self.value += 1        # LOAD → ADD → STORE  (not atomic)


def demo_race_condition():
    print("=" * 60)
    print("PART 1: Race condition — no lock")
    print("=" * 60)
    print()

    n_per_thread = 1_000_000
    n_threads    = 2
    expected     = n_per_thread * n_threads

    counter = UnsafeCounter()
    threads = [
        threading.Thread(target=counter.increment, args=(n_per_thread,))
        for _ in range(n_threads)
    ]

    t0 = time.perf_counter()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    elapsed = time.perf_counter() - t0

    lost = expected - counter.value
    pct  = lost / expected * 100

    print(f"  Threads: {n_threads},  increments each: {n_per_thread:,}")
    print(f"  Expected: {expected:,}")
    print(f"  Got:      {counter.value:,}")
    print(f"  Lost:     {lost:,}  ({pct:.1f}%)")
    print(f"  Time:     {elapsed:.3f}s")
    print()
    print("  Values will vary between runs — the race is non-deterministic.")
    print("  Sometimes you get lucky and only lose a few; other times thousands.")


# ══════════════════════════════════════════════════════════════════════════════
# PART 2: Safe counter — threading.Lock
#
# threading.Lock provides mutual exclusion:
#   - Only one thread can hold the lock at a time.
#   - All others block on lock.acquire() until the holder releases.
#
# 'with lock:' expands to lock.acquire() + try/finally lock.release()
# — safe even if the body raises an exception.
#
# Cost: every increment now requires acquiring and releasing the lock.
# This serialises access to the shared variable, reducing throughput.
# ══════════════════════════════════════════════════════════════════════════════

class SafeCounter:
    def __init__(self):
        self.value = 0
        self._lock = threading.Lock()

    def increment(self, n: int) -> None:
        for _ in range(n):
            with self._lock:       # acquire → body → release
                self.value += 1   # only one thread here at a time


def demo_safe_counter():
    print("\n" + "=" * 60)
    print("PART 2: Safe counter — threading.Lock")
    print("=" * 60)
    print()

    n_per_thread = 1_000_000
    n_threads    = 2
    expected     = n_per_thread * n_threads

    counter = SafeCounter()
    threads = [
        threading.Thread(target=counter.increment, args=(n_per_thread,))
        for _ in range(n_threads)
    ]

    t0 = time.perf_counter()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    elapsed = time.perf_counter() - t0

    print(f"  Threads: {n_threads},  increments each: {n_per_thread:,}")
    print(f"  Expected: {expected:,}")
    print(f"  Got:      {counter.value:,}")
    print(f"  Correct:  {counter.value == expected}")
    print(f"  Time:     {elapsed:.3f}s")
    print()
    print("  Always correct — but slower than the unsafe version because")
    print("  threads take turns on every increment (lock contention).")


# ══════════════════════════════════════════════════════════════════════════════
# PART 3: Minimising the locked region
#
# Locking every single increment is correct but slow.
# Better pattern: do the heavy work WITHOUT the lock, then acquire briefly:
#
#   local_sum = compute_something_expensive()  # no lock needed — local var
#   with lock:
#       shared_total += local_sum              # lock held for microseconds
#
# Here: each thread accumulates into a local variable, then adds once.
# ══════════════════════════════════════════════════════════════════════════════

class EfficientCounter:
    def __init__(self):
        self.value = 0
        self._lock = threading.Lock()

    def increment(self, n: int) -> None:
        local = 0
        for _ in range(n):
            local += 1            # no lock — local variable, thread-private

        with self._lock:          # single lock acquisition per thread
            self.value += local


def demo_efficient_counter():
    print("\n" + "=" * 60)
    print("PART 3: Minimise lock region — batch the update")
    print("=" * 60)
    print()

    n_per_thread = 1_000_000
    n_threads    = 2
    expected     = n_per_thread * n_threads

    counter = EfficientCounter()
    threads = [
        threading.Thread(target=counter.increment, args=(n_per_thread,))
        for _ in range(n_threads)
    ]

    t0 = time.perf_counter()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    elapsed = time.perf_counter() - t0

    print(f"  Threads: {n_threads},  increments each: {n_per_thread:,}")
    print(f"  Expected: {expected:,}")
    print(f"  Got:      {counter.value:,}")
    print(f"  Correct:  {counter.value == expected}")
    print(f"  Time:     {elapsed:.3f}s")
    print()
    print("  Lock acquired ONCE per thread (not 1M times).")
    print("  Orders of magnitude faster than per-increment locking.")


def main():
    demo_race_condition()
    demo_safe_counter()
    demo_efficient_counter()

    print("\n" + "=" * 60)
    print("KEY TAKEAWAYS")
    print("=" * 60)
    print()
    print("  1. Any read-modify-write on shared state is a race condition.")
    print("  2. threading.Lock serialises access — use 'with lock:' pattern.")
    print("  3. Minimise lock scope: do work locally, commit atomically.")
    print("  4. Alternatives to locks:")
    print("     - threading.Queue   — thread-safe FIFO, no lock needed by caller")
    print("     - collections.deque — thread-safe append/popleft")
    print("     - asyncio           — cooperative, single-threaded, no locking needed")


if __name__ == "__main__":
    main()

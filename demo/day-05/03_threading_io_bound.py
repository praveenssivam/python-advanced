"""
03_threading_io_bound.py
=========================
Deep dive into threading for I/O-bound workloads.

Topics:
  1. ThreadPoolExecutor map() for simple fan-out
  2. submit() + Future for heterogeneous tasks
  3. Shared-state race condition (counter corrupted without a lock)
  4. Fix: threading.Lock protects the counter

Run:
    python demo/day-05/03_threading_io_bound.py
"""

import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed


# ══════════════════════════════════════════════════════════════════════════════
# PART 1: ThreadPoolExecutor.map() — parallel I/O fan-out
#
# map(fn, iterable) submits all tasks immediately and yields results
# in the SAME ORDER as the input, blocking until each is ready.
#
# Flow for fetch_url(url_id):
#   t=0.00  all 5 tasks submitted → all start sleeping simultaneously
#   t≈0.10  all 5 complete → results yielded in input order
# ══════════════════════════════════════════════════════════════════════════════

def fetch_url(url_id: int) -> dict:
    """Simulate an HTTP GET (0.1 s latency)."""
    start = time.perf_counter()
    time.sleep(0.1)
    duration = time.perf_counter() - start
    return {"url_id": url_id, "status": 200, "duration": duration}


def demo_map():
    print("=" * 60)
    print("PART 1: ThreadPoolExecutor.map() — I/O fan-out")
    print("=" * 60)
    print()

    n = 5
    # Sequential baseline
    t0 = time.perf_counter()
    seq_results = [fetch_url(i) for i in range(n)]
    t_seq = time.perf_counter() - t0

    # Threaded with map()
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=n) as executor:
        thr_results = list(executor.map(fetch_url, range(n)))
    t_thr = time.perf_counter() - t0

    print(f"  Sequential:  {t_seq:.3f}s  ({n} requests × 0.1s)")
    print(f"  Threaded:    {t_thr:.3f}s  (all requests overlap)")
    print(f"  Speedup:     {t_seq / t_thr:.1f}×")
    print()
    print("  Results (in input order, even though they finished concurrently):")
    for r in thr_results:
        print(f"    url_id={r['url_id']}  status={r['status']}  "
              f"duration={r['duration']:.3f}s")


# ══════════════════════════════════════════════════════════════════════════════
# PART 2: as_completed() — process results as they arrive
#
# Unlike map(), as_completed() yields futures in COMPLETION ORDER.
# Useful when you want to start processing early results immediately.
#
# Flow:
#   - submit() returns a Future for each task immediately
#   - as_completed(futures) blocks until the NEXT future finishes, then yields it
#   - Results arrive in whichever order the tasks happen to finish
# ══════════════════════════════════════════════════════════════════════════════

def fetch_variable(url_id: int) -> dict:
    """Simulate requests with different latencies."""
    latency = 0.05 * (5 - url_id)   # url_id=4 finishes first (0.05s), url_id=0 last (0.25s)
    time.sleep(latency)
    return {"url_id": url_id, "latency": latency}


def demo_as_completed():
    print("\n" + "=" * 60)
    print("PART 2: as_completed() — results in arrival order")
    print("=" * 60)
    print()
    print("  Tasks have different latencies (url_id=4 fastest, url_id=0 slowest):")
    print()

    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fetch_variable, i): i for i in range(5)}
        for fut in as_completed(futures):
            result = fut.result()
            elapsed = time.perf_counter() - t0
            print(f"    [{elapsed:.2f}s]  url_id={result['url_id']} completed "
                  f"(latency={result['latency']:.2f}s)")

    print()
    print("  Notice: url_id=4 (0.05s) arrived first, url_id=0 (0.25s) last.")
    print("  With map() you would wait for url_id=0 before processing any.")


# ══════════════════════════════════════════════════════════════════════════════
# PART 3: Shared state — race condition without a lock
#
# Two threads both increment a shared counter.
# The operation looks like one step but is really LOAD → ADD → STORE.
# If the GIL switches between LOAD and STORE, both threads write back
# the same incremented value — one increment is lost.
#
# Flow (without lock):
#   thread-A: current = self.value   ← LOAD  (reads 1000)
#             --- GIL yields here, thread-B runs ---
#   thread-B: current = self.value   ← LOAD  (also reads 1000!)
#   thread-B: self.value = current+1 ← STORE (writes 1001)
#             --- GIL yields back to thread-A ---
#   thread-A: self.value = current+1 ← STORE (writes 1001 again — lost B's write!)
#
# Why self.value += 1 alone doesn't show the race on CPython 3.12:
#   The specialising interpreter fuses LOAD_ATTR + BINARY_OP + STORE_ATTR
#   into a fast path that executes in < 1 µs — faster than any GIL switch
#   interval.  Making the two steps explicit Python statements with a forced
#   yield between them guarantees the race fires on every iteration.
# ══════════════════════════════════════════════════════════════════════════════

class UnsafeCounter:
    """Counter with no synchronisation — vulnerable to race conditions."""
    def __init__(self):
        self.value = 0

    def increment(self, n: int = 1_000) -> None:
        for _ in range(n):
            current = self.value       # STEP 1 — LOAD: read shared state into local
            time.sleep(0.000_001)      # forced 1 µs yield: GIL hands off to other thread
            self.value = current + 1   # STEP 2 — STORE: write back a now-stale value


class SafeCounter:
    """Counter protected by a threading.Lock."""
    def __init__(self):
        self.value = 0
        self._lock = threading.Lock()

    def increment(self, n: int = 1_000) -> None:
        for _ in range(n):
            with self._lock:       # only one thread enters at a time
                self.value += 1


def demo_race_condition():
    print("\n" + "=" * 60)
    print("PART 3: Race condition without a lock")
    print("=" * 60)
    print()

    increments_per_thread = 1_000
    n_threads = 2
    expected = increments_per_thread * n_threads

    # --- Without lock ---
    unsafe = UnsafeCounter()
    threads = [
        threading.Thread(target=unsafe.increment, args=(increments_per_thread,))
        for _ in range(n_threads)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print(f"  Without lock  — expected: {expected:,},  got: {unsafe.value:,}")
    lost = expected - unsafe.value
    print(f"  Increments lost to race condition: {lost:,}")

    # --- With lock ---
    safe = SafeCounter()
    threads = [
        threading.Thread(target=safe.increment, args=(increments_per_thread,))
        for _ in range(n_threads)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print()
    print(f"  With lock     — expected: {expected:,},  got: {safe.value:,}")
    print(f"  Correct: {safe.value == expected}")
    print()
    print("  Key insight: any read-modify-write on shared state needs a lock.")
    print("  Lock downsides: serialises that section → reduces concurrency.")
    print("  Solution: minimise the locked region to just the shared update.")


def main():
    demo_map()
    demo_as_completed()
    demo_race_condition()


if __name__ == "__main__":
    main()

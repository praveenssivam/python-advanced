# Day 5 — Concurrency in Python

Threads, processes, and `concurrent.futures` — practical parallelism for I/O-bound and CPU-bound workloads.

---

## Learning Goals

By the end of Day 5 you will be able to:

- Explain what the GIL is and why it matters for threading
- Choose between `ThreadPoolExecutor` and `ProcessPoolExecutor` for a given workload
- Use `submit()`, `map()`, and `as_completed()` confidently
- Identify and fix race conditions with `threading.Lock`
- Apply timeout and exception-handling patterns in production futures code
- Recognise the five most common concurrency anti-patterns and their fixes

---

## Concurrency Model Comparison

| Dimension | `threading` | `multiprocessing` | `asyncio` (Day 6) |
|---|---|---|---|
| **GIL impact** | Limited for CPU | Bypasses GIL | N/A (single thread) |
| **Best for** | I/O-bound | CPU-bound | Async I/O at scale |
| **Startup cost** | Low (~1ms) | High (~100ms) | Very low |
| **Memory per worker** | ~1 MB | ~30–80 MB | ~0 MB |
| **Shared state** | Yes (needs Lock) | No (IPC only) | Yes (no lock needed) |
| **Max workers** | Hundreds | = CPU cores | Thousands |
| **Key API** | `ThreadPoolExecutor` | `ProcessPoolExecutor` | `asyncio.gather()` |

---

## File Reference

| File | Topic | Key Classes / Concepts |
|---|---|---|
| `01_concurrency_fundamentals.py` | Why concurrency, three models | sequential vs threaded vs executor baseline |
| `02_gil_concept.py` | GIL explained empirically | CPU threading (≈1×), I/O threading (≈3×), ProcessPool (≈2×) |
| `03_threading_io_bound.py` | ThreadPoolExecutor deep dive | `map()`, `as_completed()`, race condition + Lock |
| `04_multiprocessing_cpu_bound.py` | ProcessPoolExecutor | spawn overhead, chunking, 4× speedup demo |
| `05_threadpoolexecutor_basics.py` | Three submission patterns | `submit()`, `map()`, `as_completed()` on I/O tasks |
| `06_processpoolexecutor_cpu.py` | Same patterns, different engine | pickling rules, completion order |
| `07_concurrent_futures_comparison.py` | Head-to-head benchmark | I/O→Thread wins, CPU→Process wins |
| `08_timeouts_exception_handling.py` | Production robustness | `result(timeout=)`, partial success, error collection |
| `09_shared_state_locks.py` | Race conditions + Lock | corrupted counter → fixed counter → batched lock |
| `10_validation_service_concurrent.py` | Real-world pattern | `ValidationEngine` with concurrent rules |
| `11_concurrency_antipatterns.py` | What not to do | 5 anti-patterns with BAD/GOOD/WHY |

---

## Run Commands

```bash
# Run all files in order
cd /home/karthikeyan/training-temp/python-advanced

python demo/day-05/01_concurrency_fundamentals.py
python demo/day-05/02_gil_concept.py
python demo/day-05/03_threading_io_bound.py
python demo/day-05/04_multiprocessing_cpu_bound.py
python demo/day-05/05_threadpoolexecutor_basics.py
python demo/day-05/06_processpoolexecutor_cpu.py
python demo/day-05/07_concurrent_futures_comparison.py
python demo/day-05/08_timeouts_exception_handling.py
python demo/day-05/09_shared_state_locks.py
python demo/day-05/10_validation_service_concurrent.py
python demo/day-05/11_concurrency_antipatterns.py

# Verify all pass silently
for f in demo/day-05/*.py; do
  echo -n "=== $f: "
  python "$f" > /dev/null 2>&1 && echo "OK" || echo "FAIL"
done
```

---

## Trainer Flow

### Session 1 — Foundations (files 01–02, ~45 min)

1. **01**: Run it. Ask: "Which was fastest? Why?"  
   → Thread pool ≈ 5× over sequential. Introduce I/O vs CPU distinction.

2. **02**: Run parts 1 and 2 back-to-back.  
   → Part 1: ratio ≈ 1× (GIL). Part 2: ratio ≈ 3× (GIL released during sleep).  
   → Ask: "What does the GIL let go of?"  
   → Run Part 3: process pool shows the GIL escape hatch.

### Session 2 — ThreadPoolExecutor API (files 03–05, ~60 min)

3. **03**: Show `map()` output, then `as_completed()` — same work, different arrival order.  
   Then race condition demo. Ask: "Why didn't we get 200,000?" Inspect `UnsafeCounter`.

4. **04**: Sequential vs ProcessPool, emphasise spawn overhead demo (Part 3).  
   Key question: "When should you NOT use ProcessPool?"

5. **05**: Walk through all three patterns. Ask attendees to predict which arrives first  
   in `as_completed()` before running.

### Session 3 — ProcessPool + Comparison (files 06–07, ~30 min)

6. **06**: Mirror of 05 but CPU workers. Focus on pickling rules (what breaks).

7. **07**: Run I/O experiment, show ThreadPool wins. Run CPU experiment, show ProcessPool wins.  
   Build the decision table yourself on the whiteboard, then reveal.

### Session 4 — Robustness + Shared State (files 08–09, ~45 min)

8. **08**: Walk through each part. Ask: "What happens to thread-4 after TimeoutError? Is it stopped?"  
   → No — threads cannot be killed. Discuss implications (daemon threads).

9. **09**: Run unsafe counter first. Ask: "Why is it different every run?"  
   Then safe counter. Then efficient (batched) counter. Compare timings.

### Session 5 — Real App + Anti-patterns (files 10–11, ~45 min)

10. **10**: Show ValidationEngine design. Ask: "Why do we need a Lock here? (We don't — why?)"  
    → Rules only read the record. Concurrent is safe without locks.

11. **11**: Each anti-pattern: read the BAD code, predict the outcome, run it, see result.  
    Deadlock demo is the crowd-pleaser — show the detect-via-timeout approach.

---

## Optional Challenge

Extend `10_validation_service_concurrent.py`:

1. Add a `AgeRule` that sleeps 0.05s and rejects ages < 0 or > 150.
2. Modify `ConcurrentValidationEngine` to support a `fail_fast=True` option:  
   if any rule fails, cancel remaining futures and return early.  
   Hint: `Future.cancel()` only cancels futures not yet started.
3. Benchmark: with 100 records, how does sequential vs concurrent scale?

---

## Prerequisites

- Python 3.10+ (standard library only — no `pip install` needed)
- Basic understanding of functions, classes, and `with` statements
- Day 3 (SOLID) and Day 4 (Functional) patterns are referenced but not required

## What's Next

**Day 6** covers `asyncio` — Python's cooperative concurrency model.  
Where Day 5 uses threads/processes (OS-managed), Day 6 uses coroutines (Python-managed).  
`asyncio` is the right choice when you need thousands of concurrent I/O operations  
with minimal memory overhead (e.g., web servers, API gateways, streaming pipelines).

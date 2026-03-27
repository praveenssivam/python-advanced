# Day 6 — Async Python with asyncio

Cooperative concurrency using coroutines, the event loop, and the `asyncio` standard library.

---

## Learning Goals

By the end of Day 6 you will be able to:

- Explain the difference between calling and awaiting a coroutine
- Describe the event loop and cooperative scheduling
- Choose the right concurrent pattern: `gather()`, `create_task()`, `as_completed()`
- Write async context managers with `__aenter__`/`__aexit__`
- Apply timeout and retry patterns to production async code
- Use `asyncio.Semaphore` to throttle concurrent access
- Safely mix synchronous and asynchronous code with `run_in_executor()`
- Recognise the six most common async anti-patterns

---

## Async vs Threading (Day 5)

| Dimension | `asyncio` (Day 6) | `threading` (Day 5) |
|---|---|---|
| **Concurrency model** | Cooperative (yield with `await`) | Pre-emptive (OS switches) |
| **Thread count** | 1 thread | N threads |
| **GIL impact** | N/A — no thread switching | Limits CPU-bound work |
| **Best for** | I/O-bound, many connections | I/O-bound, blocking libraries |
| **Memory per task** | ~1–2 KB | ~1–2 MB |
| **Max concurrent** | Tens of thousands | Hundreds |
| **Shared state** | `asyncio.Lock()` needed at yields | `threading.Lock()` always |
| **Blocking danger** | `time.sleep()` freezes ALL tasks | Only blocks one thread |

**Rule of thumb:**
- Async scales better for I/O at high concurrency (>100 connections)
- Threads are simpler for small concurrency or legacy blocking libraries
- CPU-bound: neither — use `ProcessPoolExecutor` (Day 5)

---

## Pattern Selection Guide

| Situation | Pattern |
|---|---|
| N independent tasks, need all results | `asyncio.gather(*coros)` |
| N tasks, process each result on arrival | `asyncio.as_completed(coros)` |
| Need to cancel or monitor a task | `asyncio.create_task(coro)` |
| Background task running while main continues | `create_task()` without immediate await |
| Per-coroutine timeout | `asyncio.wait_for(coro, timeout=N)` |
| Batch timeout (all tasks share one deadline) | `wait_for(gather(*coros), timeout=N)` |
| Limit simultaneous resource use | `asyncio.Semaphore(N)` |
| Async resource with cleanup | `async with AsyncResource() as r:` |
| Call blocking code from async | `await loop.run_in_executor(pool, fn, x)` |
| Run async from synchronous code | `asyncio.run(coro)` |

---

## File Reference

| File | Topic | Key Concepts |
|---|---|---|
| `01_async_basics.py` | Coroutines and the event loop | call vs await, `asyncio.run()`, cooperative scheduling |
| `02_asyncio_patterns.py` | Four concurrency patterns | sequential, `create_task`, `gather`, `as_completed` |
| `03_async_io_operations.py` | Three I/O types | network, file, DB simulation; 20 ops in 0.12s |
| `04_async_concurrent_requests.py` | 10 concurrent requests | sequential vs gather, progress tracking, cancel |
| `05_asyncio_gather_patterns.py` | `gather()` deep dive | exceptions, `return_exceptions`, timeouts |
| `06_async_context_managers.py` | `__aenter__`/`__aexit__` | class-based, `@asynccontextmanager`, connection pool |
| `07_async_timeout_handling.py` | Timeouts and retry | `wait_for()`, fallback, retry with backoff |
| `08_async_semaphore_rate_limiting.py` | Semaphore and rate limiting | bounded concurrency, token bucket |
| `09_mixing_sync_async.py` | Sync ↔ async bridge | `run_in_executor()`, `asyncio.run()` |
| `10_async_validation_service.py` | Real-world async app | concurrent rules, 10 concurrent clients |
| `11_async_antipatterns.py` | What not to do | 6 anti-patterns with BAD/GOOD/WHY |

---

## Run Commands

```bash
cd /home/karthikeyan/training-temp/python-advanced

python demo/day-06/01_async_basics.py
python demo/day-06/02_asyncio_patterns.py
python demo/day-06/03_async_io_operations.py
python demo/day-06/04_async_concurrent_requests.py
python demo/day-06/05_asyncio_gather_patterns.py
python demo/day-06/06_async_context_managers.py
python demo/day-06/07_async_timeout_handling.py
python demo/day-06/08_async_semaphore_rate_limiting.py
python demo/day-06/09_mixing_sync_async.py
python demo/day-06/10_async_validation_service.py
python demo/day-06/11_async_antipatterns.py

# Verify all pass silently
for f in demo/day-06/*.py; do
  echo -n "=== $f: "
  python "$f" > /dev/null 2>&1 && echo "OK" || echo "FAIL"
done
```

---

## Trainer Flow

### Session 1 — How async works (files 01–02, ~45 min)

1. **01**: Before running, ask: "What does calling `hello()` return without `await`?"  
   → Run it. Show the coroutine object. Then show `await` gives the result.  
   Run Part 3 (cooperative scheduling). Ask: "How are tasks running if Python is single-threaded?"

2. **02**: Run pattern 1 (sequential) — 0.3s. "Why is this slow even though it's async?"  
   → Missing parallelism. Run pattern 3 (gather) — 0.1s. "What changed?"  
   → All coroutines were submitted at once. Run pattern 4 (as_completed) with varied delays.

### Session 2 — Concurrency patterns (files 03–05, ~60 min)

3. **03**: "Count the outputs — did all 5 ops really run simultaneously?"  
   → Yes. Scale to 20 (Part 4). "Did it get slower?" → No. Why? Bounded by slowest, not count.

4. **04**: The sequential async anti-pattern (Part 1) is the moment everyone says "oh!"  
   → Run it. "It's async code, why is it sequential?" → `await` in a for-loop.

5. **05**: Walk through each gather pattern. Pause on `return_exceptions=True`:  
   "What would happen without this?" → Run Part 2 (exception propagation) first.  
   Then show Part 3 as the fix.

### Session 3 — Resource management (files 06–07, ~45 min)

6. **06**: Walk through the `AsyncDatabase` class. Ask attendees to predict what prints.  
   Run the exception path — show `__aexit__` still runs. "Where does this guarantee come from?"  
   → `try/finally` structure in the context manager protocol.

7. **07**: Run Case B (timeout). Ask: "Is the task cancelled or abandoned?"  
   → Cancelled (CancelledError sent in). Show Part 2 (fallback) — the real production pattern.

### Session 4 — Control (files 08–09, ~45 min)

8. **08**: Run Part 1 (no semaphore) — peak=20. Run Part 2 (semaphore 5) — peak=5.  
   "When would unbounded concurrent connections cause a production incident?"

9. **09**: The blocking sleep anti-pattern (Part 1) is visceral: 0.45s vs 0.15s.  
   "What exactly is frozen?" → The event loop thread. Run `run_in_executor` for both cases.

### Session 5 — Real app + Anti-patterns (files 10–11, ~45 min)

10. **10**: Compare per-record timing. Ask: "In Part 3, 10 clients all sent at once — why is total ~0.1s?"  
    → Each client's validation rules run concurrently; clients themselves overlap.

11. **11**: Walk each anti-pattern in order. Anti-pattern 1 (missing `await`) gets the RuntimeWarning.  
    Anti-pattern 5 (race condition) is the surprise — "but asyncio is single-threaded!"  
    → Single-threaded doesn't mean atomic. Yields between read and write are still races.

---

## Optional Challenge

Extend `10_async_validation_service.py`:

1. Add an `AsyncAgeRule` that:
   - Awaits 0.06s (simulate age verification API call)
   - Rejects ages outside [0, 150]

2. Add a per-rule timeout of 0.15s using `asyncio.wait_for()` in `ConcurrentAsyncEngine`.  
   If a rule times out, its `RuleResult.passed = False` with an appropriate message.

3. Add an `asyncio.Semaphore(3)` to `ConcurrentAsyncEngine` — limit to 3 rules per record  
   running concurrently (artificially, to demonstrate the pattern).

4. Benchmark: validate 100 records with all 4 rules using the concurrent engine.  
   Expected: ~0.10s total (bounded by slowest rule, regardless of record count).

---

## Prerequisites

- Python 3.10+ (standard library only)
- Basic understanding of functions, classes, exceptions
- Day 5 (Concurrency) gives important context but is not strictly required

## Day 5 vs Day 6 — When to Use Each

```
I/O-bound + few connections  (< 50)   → ThreadPoolExecutor (simpler)
I/O-bound + many connections (> 100)  → asyncio (memory efficient)
CPU-bound                              → ProcessPoolExecutor
Blocking legacy libraries              → run_in_executor + ThreadPool
Mixed CPU + I/O                        → asyncio + run_in_executor for CPU parts
```

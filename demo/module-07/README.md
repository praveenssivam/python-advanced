# Module 7 — Performance Engineering

Profile first. Optimize second. Measure the improvement. Repeat.

---

## Learning Goals

By the end of Module 7 you will be able to:

- Use `timeit` to establish reproducible performance baselines
- Run `cProfile` on a specific code path and read the `pstats` output
- Interpret `ncalls`, `tottime`, and `cumtime` to locate the real bottleneck
- Distinguish deterministic profilers (`cProfile`) from sampling profilers (`py-spy`)
- Fix the two most common Python hotspots: regex re-compilation and repeated expensive calls
- Measure memory allocation sites with `tracemalloc`
- Apply five optimization patterns: algorithm, built-ins, caching, batching, lazy evaluation
- Recognise five common performance anti-patterns

---

## The Performance Workflow

```
Observe slow behavior
        ↓
Define a measurable target  (e.g. "batch of 500 records < 10ms")
        ↓
Establish baseline with timeit
        ↓
Profile with cProfile → find hotspot #1
        ↓
Apply the matching optimization pattern
        ↓
Re-measure with timeit — confirm improvement
        ↓
Profile again → find hotspot #2 (if still needed)
        ↓
Stop when the target is met
```

**Never optimize without first measuring. Profile output is the only authority.**

---

## Key `pstats` Columns

| Column | Meaning | When it matters |
|---|---|---|
| `ncalls` | Number of calls | `ncalls == batch_size` → needs caching or batching |
| `tottime` | Time in function body only | High tottime → function itself is CPU-bound |
| `percall` | `tottime / ncalls` | Per-call cost of the function body |
| `cumtime` | `tottime + all sub-call time` | Best first sort — owns the most wall-clock time |

**Sort by `cumtime` first.** If `cumtime` is high but `tottime` is low, the cost is in callees — drill down.

---

## Five Optimization Patterns

| # | Pattern | When to apply | Speedup range |
|---|---|---|---|
| 1 | Better algorithm | `ncalls` grows quadratically with N | 10–10,000× |
| 2 | Built-in substitution | Python loop where a C-backed function exists (`sum`, `sorted`, etc.) | 2–5× |
| 3 | `lru_cache` | Pure function, repeated inputs, bounded input space | 10–1000× |
| 4 | Batching | `ncalls == batch_size` for an I/O call with fixed overhead | proportional to N |
| 5 | Lazy / generators | Pipeline with large intermediate collections | Memory reduction |

---

## File Reference

| File | Topic | Key Concepts |
|---|---|---|
| `01_timeit_benchmarking.py` | Baselines | `timeit.timeit`, `timeit.repeat`, take the minimum |
| `02_cprofile_basics.py` | cProfile in code | `Profile.enable/disable`, `pstats.Stats`, `print_callers` |
| `03_regex_bottleneck.py` | Hotspot fix: regex | `re.compile` at module level, before/after profile |
| `04_lru_cache_optimization.py` | Hotspot fix: cache | `@lru_cache`, `cache_info()`, when NOT to cache |
| `05_generators_vs_lists.py` | Memory vs speed | `tracemalloc` memory, lazy pipeline, generator gotchas |
| `06_tracemalloc_memory_profiling.py` | Memory profiling | Snapshot comparison, peak usage, `__slots__` |
| `07_optimization_patterns.py` | All 5 patterns | Measured before/after for each pattern |
| `08_performance_antipatterns.py` | What not to do | 5 anti-patterns with cost measurements |
| `09_py_spy_simulation.py` | Sampling profiler | py-spy commands, flame graph reading guide |
| `10_before_after_workflow.py` | Full workflow | End-to-end: baseline → profile → fix × 2 → report |

---

## Run Commands

```bash
cd /home/karthikeyan/training-temp/python-advanced

python demo/module-07/01_timeit_benchmarking.py
python demo/module-07/02_cprofile_basics.py
python demo/module-07/03_regex_bottleneck.py
python demo/module-07/04_lru_cache_optimization.py
python demo/module-07/05_generators_vs_lists.py
python demo/module-07/06_tracemalloc_memory_profiling.py
python demo/module-07/07_optimization_patterns.py
python demo/module-07/08_performance_antipatterns.py
python demo/module-07/09_py_spy_simulation.py
python demo/module-07/10_before_after_workflow.py

# Verify all pass
for f in demo/module-07/*.py; do
  echo -n "=== $f: "
  python "$f" > /dev/null 2>&1 && echo "OK" || echo "FAIL"
done
```

---

## Trainer Flow

### Session 1 — Measure first (files 01–02, ~50 min)

1. **01**: Run Part 1. Ask: "What does `timeit.timeit` return — per call or total?"
   → Total. Divide by `number`. Then run Part 2 (repeat). "Why take the minimum?"
   → Noise goes up, never down. Minimum eliminates OS scheduling variance.
   Run Part 3 — `slow_validate` vs `fast_validate`. "What's changing between them?"
   → Pause. Don't answer. Run Part 4 to introduce the SLA concept.

2. **02**: "We're going to find out exactly what changed." Run Part 1 — show the raw
   cProfile dump. Walk each column. Pause on `ncalls`. "What does
   `ncalls ≈ 200` mean for `re.fullmatch`?"
   → It ran 200 times — once per record. That's the bottleneck pattern.

### Session 2 — Fix common hotspots (files 03–04, ~50 min)

3. **03**: Run Part 1. Find `re.fullmatch` in the output. "Where is it in the list?"
   → Near the top. "What does `ncalls = batch_size` tell us?"
   → Pattern is being processed on every single call.
   Run Part 2 (compiled). "Where did the re overhead go?"
   → Eliminated. Run Part 3 (benchmark) — show the speedup ratio.

4. **04**: Run Part 1. "What do you notice about `ncalls` for `load_schema`?"
   → ncalls = 100. 100 records, 3 schemas. 97 calls were wasted.
   Run Part 2 (cached). Show `cache_info()`. Run Part 3 (benchmark).
   Key moment: run Part 4 — the unbounded key example. "Why does hit rate stay 0%?"
   → Every user_id is unique — the cache just evicts and recreates constantly.

### Session 3 — Memory and pipelines (files 05–06, ~45 min)

5. **05**: Run Part 1. Ask before running: "How big is a generator vs a list?"
   → Show the answer. Then run Part 2 (pipeline). "How does this scale?"
   → O(1) memory regardless of N. Run Part 4 (gotchas) — highlight the
   "iterate twice" trap.

6. **06**: Run Part 2 (snapshot comparison). "When is memory the right thing to optimize?"
   → When GC pauses cause CPU spikes visible in py-spy. Run Part 3 (peak).

### Session 4 — Patterns and anti-patterns (files 07–08, ~50 min)

7. **07**: Run each pattern demo in order. For Pattern 1 (algorithm), show the speedup
   table at N=5000. "Why does the speedup grow with N?"
   → O(n²) vs O(n) — gap widens proportionally. For Pattern 4 (batching),
   emphasise the security note: **always parameterised queries**.

8. **08**: Anti-pattern 1 is the opener — show `looks_slow` vs `actually_slow`.
   "Which would you optimize first?" Let them guess. Then run it.
   Anti-pattern 2 (string concat) is visceral — explain the O(n²) allocation cost.
   Anti-pattern 5 (exceptions): "exceptions should be exceptional".

### Session 5 — Full workflow (files 09–10, ~45 min)

9. **09**: This is the py-spy reference demo. Walk through the commands in Part 2.
   Ask: "What would you look for in py-spy top?" → wide bars, high OwnTime.
   Walk the flame graph diagram in Part 3 — map it to cProfile output from file 02.

10. **10**: This is the capstone. Run it live. Stop after each STEP and ask:
    "What's the next action?" Pause after STEP 3 profile — "what do you fix first?"
    → Largest cumtime. After STEP 5 profile — "is the regex still there?"
    → No. "What's the new top?"  Read the FINAL REPORT together.

---

## Optional Challenge

Profile the capstone validation service from `capstone/validify/`:

1. Add a `timeit` baseline for `validate_batch(load_all_records())`.
2. Wrap it in `cProfile.Profile()` and save to `validify.prof`.
3. Run `pstats` and find the top 3 functions by `cumtime`.
4. Apply the appropriate pattern to hotspot #1 only.
5. Re-run `timeit` and compute the speedup ratio.
6. Target: achieve ≥ 2× speedup on the batch median.

---

## Prerequisites

- Python 3.10+ (standard library only: `cProfile`, `pstats`, `timeit`, `tracemalloc`, `functools`, `re`)
- `py-spy` requires: `pip install py-spy` (only needed for actual production profiling)
- Days 1–6 recommended but not strictly required

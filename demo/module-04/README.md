# Module 4 — Functional Programming in Python

## Overview

Functional programming (FP) treats computation as the **evaluation of pure functions** — functions that always return the same result for the same input and never modify external state.

Python is a multi-paradigm language, so you don't need to go "full FP". The goal is to borrow the best FP ideas and add them to your OOP toolkit.

---

## Learning Goals

By the end of Module 4 you will be able to:

- Store functions in variables and pass them as arguments to other functions
- Understand what a **closure** captures and when to use `nonlocal`
- Create specialised functions from general ones using `functools.partial`
- Reduce a sequence to a single value using `functools.reduce` and know when to prefer `sum`/`max` instead
- Eliminate repeated computation using `@lru_cache` and read `cache_info()`
- **Compose** single-purpose functions into a data pipeline
- Explain what **immutability** means in Python and apply `{**dict, k: v}` and `[*list, item]` patterns
- Contrast list comprehensions with generator expressions and explain the memory difference
- Compare OOP, pure-functional, and hybrid approaches to the same problem
- Combine closures, partial, lru_cache, composition, immutability, and generators into a complete pipeline

---

## Files

| File | Topic | Key technique |
|---|---|---|
| `01_first_class_functions.py` | Functions as first-class values | Variables, higher-order fns, dispatch table |
| `02_closures.py` | Capturing variables from enclosing scope | `nonlocal`, configurable validators |
| `03_functools_partial.py` | Binding arguments in advance | `functools.partial`, comparison with lambda |
| `04_functools_reduce.py` | Folding a sequence to a value | `functools.reduce`, traced reduce |
| `05_functools_lru_cache.py` | Memoisation | `@lru_cache`, `cache_info()`, fibonacci |
| `06_function_composition.py` | Building pipelines from functions | `pipe()`, `compose()`, predicate composition |
| `07_immutability.py` | Treating data as immutable | `{**d, k: v}`, `[*l, item]`, NamedTuple |
| `08_generators_vs_lists.py` | Lazy vs eager evaluation | Generator expressions, `yield`, chained generators |
| `09_functional_vs_oop.py` | Same problem — three styles | OOP class, pure functions, `@dataclass` + functions |
| `10_combined_functional_patterns.py` | Everything combined | Full lazy pipeline using all Module 4 techniques |

---

## Running the Demos

Run from the repository root:

```bash
cd /path/to/python-advanced

python demo/module-04/01_first_class_functions.py
python demo/module-04/02_closures.py
python demo/module-04/03_functools_partial.py
python demo/module-04/04_functools_reduce.py
python demo/module-04/05_functools_lru_cache.py
python demo/module-04/06_function_composition.py
python demo/module-04/07_immutability.py
python demo/module-04/08_generators_vs_lists.py
python demo/module-04/09_functional_vs_oop.py
python demo/module-04/10_combined_functional_patterns.py
```

---

## Technique Quick Reference

### First-class functions

```python
def double(x): return x * 2
transform = double          # assign
transform(5)                # → 10
[f(3) for f in [double]]    # store in list
```

### Closures

```python
def make_multiplier(factor):
    def multiply(x):
        return x * factor   # captures `factor`
    return multiply

triple = make_multiplier(3)
triple(5)   # → 15
```

### `functools.partial`

```python
from functools import partial

def power(base, exp): return base ** exp
square = partial(power, exp=2)
square(5)   # → 25
```

### `functools.reduce`

```python
from functools import reduce
reduce(lambda acc, x: acc + x, [1, 2, 3, 4], 0)   # → 10
```

### `@lru_cache`

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def fib(n):
    return n if n < 2 else fib(n-1) + fib(n-2)

fib(30)                # computed once
fib.cache_info()       # CacheInfo(hits=..., misses=..., ...)
```

### Function composition

```python
from functools import reduce

def pipe(*fns):
    return lambda v: reduce(lambda x, f: f(x), fns, v)

normalise = pipe(str.strip, str.lower)
normalise("  HELLO  ")   # → "hello"
```

### Immutable dict / list update

```python
record = {"id": 1, "status": "raw"}
updated = {**record, "status": "validated"}   # new dict
record                                          # unchanged
```

### Generators

```python
# Lazy: nothing computed yet
gen = (x * 2 for x in range(1_000_000))

# vs eager: all in memory now
lst = [x * 2 for x in range(1_000_000)]
```

---

## When to Use Each Technique

| Technique | Best for | Avoid when |
|---|---|---|
| **Closures** | Configurable callbacks, validators | State that grows complex (use a class) |
| **partial** | Pre-binding 1–2 args in pipelines | Many keyword args (use a class or config dict) |
| **reduce** | Custom fold logic | When `sum()`, `max()`, or `any()` already does the job |
| **lru_cache** | Expensive pure lookups called many times | Functions with side effects or mutable args |
| **pipe/compose** | Multi-step transform chains | Very long chains that benefit from named intermediate steps |
| **Immutability** | Functions shared across threads, unit tests | Performance-critical tight loops on large data |
| **Generators** | Large / infinite sequences, lazy pipelines | When random access or `len()` is needed |

---

## What to Observe

| Demo | Watch for |
|---|---|
| `01_first_class_functions.py` | `function.__name__` and `function.__doc__` exist on the function object |
| `02_closures.py` | `make_counter()` uses `nonlocal` to modify captured state across calls |
| `03_functools_partial.py` | `partial.func` and `partial.keywords` reveal what was bound |
| `05_functools_lru_cache.py` | `[COMPUTING]` prints only on the first call for each argument |
| `08_generators_vs_lists.py` | `sys.getsizeof(generator)` = ~120 bytes regardless of range size |
| `10_combined_functional_patterns.py` | `[LOOKUP]` prints only once per unique zone code |

---

## Trainer Flow

1. **`01` → `02`** — convince students that closures feel like "functions with memory"
2. **`03` → `04`** — partial and reduce are just convenient building blocks for pipelines
3. **`05`** — show the fibonacci call-count contrast; emphasise "pure functions only"
4. **`06`** — use the column-normaliser to motivate composition
5. **`07`** — run the mutable BEFORE immutable, then ask "who changed my data?"
6. **`08`** — the `getsizeof` comparison is memorable; then show the lazy-evaluation step-by-step
7. **`09`** — same problem three ways; discuss team preference, not "which is right"
8. **`10`** — tie everything together; trace the full pipeline on one record on a whiteboard

---

## Optional Challenge

Extend `10_combined_functional_patterns.py`:

1. Add a **`split_by_zone`** generator that groups the output records into a dict
   `{"north": [...], "south": [...], ...}` using only generators and immutable updates.

2. Write a **`make_discount_enricher(threshold, discount_pct)`** closure factory that
   adds `"discount": 0.10` to records where `fare > threshold`, using partial to
   create `enrich_high_value = make_discount_enricher(20.0, 0.10)`.

3. Add a **`@lru_cache`-backed `get_driver_tier(trip_id_prefix)`** function that
   simulates looking up whether a driver prefix (e.g. `"T0"`) is a platinum/gold/silver tier.

---

## Key Takeaways

- **First-class functions**: functions are values — store them, pass them, build them dynamically.
- **Closures** create configurable callables without classes; `nonlocal` enables mutable captured state.
- **`partial`** fixes arguments in advance — equivalent to a one-line closure without the boilerplate.
- **`reduce`** generalises any fold operation; prefer `sum`/`max` when the specialised built-in exists.
- **`lru_cache`** is `O(1)` memoisation for pure functions with hashable arguments.
- **Function composition** makes a multi-step pipeline look like a single transformation.
- **Immutability** prevents silent mutation bugs at the cost of extra object allocations.
- **Generators** trade memory for laziness — essential for large data that doesn't fit in RAM.
- Python is multi-paradigm: mix OOP and FP as the problem demands, not as an ideology.

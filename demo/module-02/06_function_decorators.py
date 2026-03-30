"""
06_function_decorators.py
===========================
Demonstrates function decorators:
  - A minimal decorator that wraps a function
  - Timing and logging decorators
  - Why functools.wraps matters (preserving __name__ and __doc__)
  - Stacking multiple decorators
  - A decorator factory that accepts arguments

Run:
    python module-02/06_function_decorators.py
"""

import time
import functools


# ══════════════════════════════════════════════════════════════════════════════
# PART 1: Minimal decorator — the pattern made explicit
#
# A decorator is a function that:
#   1. Receives another function as its argument.
#   2. Defines a wrapper function that adds behaviour before/after.
#   3. Returns the wrapper (a plain function object).
#
# The `@make_loud` syntax is syntactic sugar for:  add = make_loud(add)
# After that line, `add` IS `wrapper`. Every future call to add() goes
# through wrapper, which calls the original func internally.
#
# Execution flow for  add(3, 4)  after decoration:
#   add(3, 4)
#   → wrapper(3, 4)              (‘add’ now refers to wrapper)
#   → prints "→ calling add"
#   → result = func(3, 4)        (func is the ORIGINAL add, captured by closure)
#   → prints "← add returned 7"
#   → returns 7
# ══════════════════════════════════════════════════════════════════════════════

def make_loud(func):
    """Wrap func to announce its call and return value.

    func is captured in the wrapper's closure — it lives as long as wrapper
    does, even after make_loud() has returned.
    """

    def wrapper(*args, **kwargs):
        print(f"  → calling {func.__name__}")
        result = func(*args, **kwargs)  # call the original function
        print(f"  ← {func.__name__} returned {result!r}")
        return result  # always return so callers still get the value

    return wrapper


@make_loud
def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b


def demo_minimal_decorator():
    print("=" * 55)
    print("PART 1: Minimal decorator")
    print("=" * 55)

    # At this point `add` IS `wrapper` (the name was rebound at definition time)
    result = add(3, 4)
    print(f"Final result: {result}")
    print()
    # Make the equivalence explicit for learners:
    print("The @make_loud syntax is equivalent to:")
    print("  add = make_loud(add)")


# ══════════════════════════════════════════════════════════════════════════════
# PART 2: functools.wraps — preserving function identity
#
# Without @functools.wraps, `wrapper.__name__` is literally "wrapper" and
# `wrapper.__doc__` is None. This breaks:
#   - help(), docstrings, auto-generated API docs
#   - unittest.mock assertions that check function names
#   - any debugging tool that reads __name__ or __qualname__
#
# @functools.wraps(func) copies these attributes from func onto wrapper:
#   __name__, __qualname__, __doc__, __module__, __dict__, __wrapped__
#
# The extra __wrapped__ attribute lets you unwrap decorators to reach the
# original function (used by inspect.unwrap()).
# ══════════════════════════════════════════════════════════════════════════════

def timing_without_wraps(func):
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"  [{func.__name__}] took {elapsed * 1000:.3f} ms")
        return result
    return wrapper


def timing(func):
    @functools.wraps(func)  # copies __name__, __doc__, __module__, __qualname__
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"  [{func.__name__}] took {elapsed * 1000:.3f} ms")
        return result
    return wrapper


@timing_without_wraps
def compute_without(n: int) -> int:
    """Sum integers up to n."""
    return sum(range(n))


@timing
def compute(n: int) -> int:
    """Sum integers up to n."""
    return sum(range(n))


def demo_functools_wraps():
    print("\n" + "=" * 55)
    print("PART 2: functools.wraps — preserving function identity")
    print("=" * 55)

    compute_without(100_000)
    compute(100_000)

    print()
    print(f"Without @functools.wraps:")
    print(f"  __name__ = {compute_without.__name__!r}")    # 'wrapper' — wrong
    print(f"  __doc__  = {compute_without.__doc__!r}")     # None — lost

    print()
    print(f"With @functools.wraps:")
    print(f"  __name__ = {compute.__name__!r}")            # 'compute' — correct
    print(f"  __doc__  = {compute.__doc__!r}")             # preserved


# ══════════════════════════════════════════════════════════════════════════════
# PART 3: Logging decorator
#
# A real-world decorator that logs calls, results, and exceptions.
# Demonstrates the full wrapper pattern:
#   - Capture args/kwargs for logging before the call.
#   - Use try/except inside the wrapper to intercept any exception,
#     log it, then re-raise so callers still see the error.
# ══════════════════════════════════════════════════════════════════════════════

def log_call(func):
    """Log function entry, exit, and any exception raised.

    Flow for a successful call:
      CALL divide(10, 4)  ← logged before calling
      OK   divide → 2.5   ← logged after returning

    Flow for a failing call:
      CALL divide(10, 0)
      ERROR divide raised ZeroDivisionError: ...  ← logged, then re-raised
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        arg_str = ", ".join(
            [repr(a) for a in args] + [f"{k}={v!r}" for k, v in kwargs.items()]
        )
        print(f"  CALL  {func.__name__}({arg_str})")
        try:
            result = func(*args, **kwargs)
            print(f"  OK    {func.__name__} → {result!r}")
            return result
        except Exception as e:
            print(f"  ERROR {func.__name__} raised {type(e).__name__}: {e}")
            raise

    return wrapper


@log_call
def divide(a: float, b: float) -> float:
    """Divide a by b."""
    if b == 0:
        raise ZeroDivisionError("b cannot be zero")
    return a / b


def demo_logging_decorator():
    print("\n" + "=" * 55)
    print("PART 3: Logging decorator")
    print("=" * 55)

    divide(10, 4)
    try:
        divide(10, 0)
    except ZeroDivisionError:
        pass  # already logged by decorator


# ══════════════════════════════════════════════════════════════════════════════
# PART 4: Decorator factory — decorator that accepts arguments
#
# When a decorator needs configuration (e.g. max_attempts=3), you add
# one more level of nesting:
#
#   retry(max_attempts=3)         ← outer call returns the decorator
#   decorator(func)               ← decorator receives the function
#   wrapper(*args, **kwargs)      ← wrapper is what actually runs each call
#
# Three levels: factory → decorator → wrapper
#
# The @retry(max_attempts=3) syntax is equivalent to:
#   flaky_fetch = retry(max_attempts=3)(flaky_fetch)
# ══════════════════════════════════════════════════════════════════════════════

def retry(max_attempts: int = 3, delay_sec: float = 0.0):
    """Decorator factory: retry a function up to max_attempts times on exception.

    Nesting summary:
      retry(3, 0.0)   → returns `decorator`  (closes over max_attempts, delay_sec)
      decorator(func) → returns `wrapper`    (closes over func)
      wrapper(...)    → runs func in a retry loop
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exc = e
                    print(f"  Attempt {attempt}/{max_attempts} failed: {e}")
                    if attempt < max_attempts and delay_sec > 0:
                        time.sleep(delay_sec)
            raise last_exc  # type: ignore

        return wrapper

    return decorator


_call_count = 0  # module-level counter to simulate flaky behaviour


@retry(max_attempts=3)
def flaky_fetch(url: str) -> str:
    """Simulates a function that fails the first two times."""
    global _call_count
    _call_count += 1
    if _call_count < 3:
        raise ConnectionError(f"Could not reach {url}")
    return f"<data from {url}>"


def demo_decorator_factory():
    print("\n" + "=" * 55)
    print("PART 4: Decorator factory with arguments")
    print("=" * 55)

    result = flaky_fetch("https://api.example.com/data")
    print(f"Final result: {result!r}")


# ══════════════════════════════════════════════════════════════════════════════
# PART 5: Stacking decorators
#
# When you stack decorators, they apply BOTTOM-UP at definition time:
#
#   @log_call
#   @timing
#   def process_batch(...): ...
#
# is equivalent to:
#   process_batch = log_call(timing(process_batch))
#
# So the call order at runtime is TOP-DOWN:
#   process_batch(...)  →  log_call’s wrapper runs first
#                        →  it calls timing’s wrapper
#                            →  which calls the original process_batch
#                            ←  timing prints elapsed
#                        ←  log_call prints OK + result
# ══════════════════════════════════════════════════════════════════════════════

@log_call
@timing
def process_batch(batch_id: str, size: int) -> dict:
    """Process a batch of records."""
    time.sleep(0.001)  # simulate work
    return {"batch_id": batch_id, "processed": size}


def demo_stacking():
    print("\n" + "=" * 55)
    print("PART 5: Stacking decorators")
    print("=" * 55)

    print("Decorators apply bottom-up: timing wraps process_batch first,")
    print("then log_call wraps the already-timed version.\n")
    process_batch("B-042", 500)


def main():
    demo_minimal_decorator()
    demo_functools_wraps()
    demo_logging_decorator()
    demo_decorator_factory()
    demo_stacking()


if __name__ == "__main__":
    main()

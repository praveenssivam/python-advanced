"""
05_context_managers.py
=======================
Demonstrates deterministic resource cleanup using context managers:
  - Class-based: __enter__ and __exit__
  - Function-based: contextlib.contextmanager
  - How __exit__ is called even when an exception is raised
  - Suppressing exceptions inside __exit__

Run:
    python module-02/05_context_managers.py
"""

import time
import contextlib


# ══════════════════════════════════════════════════════════════════════════════
# PART 1: Class-based context manager
#
# How the `with` statement works:
#
#   with SomeContextManager() as x:
#       <body>
#
#   1. Python calls SomeContextManager().__enter__().
#      The return value is bound to `x`.
#   2. The <body> executes.
#   3. Python calls __exit__(exc_type, exc_val, exc_tb) unconditionally —
#      whether the body finished normally OR raised an exception.
#      exc_type is None if no exception occurred.
#   4. If __exit__ returns True, any exception is suppressed.
#      If it returns False (or None), the exception propagates.
#
# The guarantee: __exit__ ALWAYS runs — equivalent to a try/finally block,
# but expressed as a reusable, composable object.
# ══════════════════════════════════════════════════════════════════════════════

class ManagedConnection:
    """Simulates a database connection that must always be closed.

    __enter__: acquire the resource, return self (binds to the `as` variable).
    __exit__ : release the resource. The three parameters describe any exception
               that occurred in the body (all None if no exception).

    Returning False from __exit__ lets exceptions propagate normally.
    Returning True from __exit__ suppresses the exception (see PART 3).
    """

    def __init__(self, host: str, port: int = 5432):
        self.host = host
        self.port = port
        self._open = False

    def __enter__(self):
        # Called when the `with` block is entered.
        # Returns self so `with ... as conn` binds the connection to `conn`.
        print(f"  [open]  Connecting to {self.host}:{self.port}")
        self._open = True
        return self  # the value bound by `as`

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Called unconditionally: after normal completion AND after exceptions.
        # exc_type is None when the body completed without raising.
        print(f"  [close] Disconnecting from {self.host}:{self.port}")
        self._open = False
        # Return False (or None): exception propagates to the caller.
        # Return True: exception is silently discarded.
        return False

    def query(self, sql: str) -> list:
        if not self._open:
            raise RuntimeError("Connection is not open.")
        print(f"  [query] {sql}")
        return [{"id": 1}, {"id": 2}]  # simulated result


def demo_class_context_manager():
    print("=" * 55)
    print("PART 1: Class-based context manager")
    print("=" * 55)

    print("\n--- Normal usage ---")
    # Flow:
    #   1. ManagedConnection("db.example.com").__enter__() → prints [open], returns conn
    #   2. Body executes: conn.query(...)
    #   3. Body completes normally → __exit__(None, None, None) → prints [close]
    with ManagedConnection("db.example.com") as conn:
        results = conn.query("SELECT id FROM events LIMIT 2")
        print(f"  [result] {results}")
    print("Connection closed after the with block — even without explicit close().")

    print("\n--- Exception inside with block ---")
    # Flow:
    #   1. __enter__() → prints [open], returns conn
    #   2. Body raises ValueError
    #   3. __exit__(ValueError, <exc>, <tb>) → prints [close], returns False
    #   4. False → exception propagates to the outer try/except
    try:
        with ManagedConnection("db.example.com") as conn:
            conn.query("SELECT * FROM events")
            raise ValueError("Downstream processing failed")
    except ValueError as e:
        print(f"  [caught] {e}")
    print("__exit__ was still called — resource was released despite the error.")


# ══════════════════════════════════════════════════════════════════════════════
# PART 2: Function-based context manager with @contextmanager
#
# @contextmanager turns a generator function into a context manager.
# The anatomy of the generator:
#
#   Code BEFORE yield  ←→ equivalent to __enter__
#   The `yield` expression  ←→ the value bound by `as`
#   Code AFTER yield (in finally) ←→ equivalent to __exit__
#
# Use a try/finally around the yield to guarantee cleanup even on exception.
# This is more compact than writing a full class for simple cases.
# ══════════════════════════════════════════════════════════════════════════════

@contextlib.contextmanager
def managed_file_writer(path: str):
    """Open a file for writing and ensure it is closed."""
    print(f"  [open]  Opening {path} for writing")
    handle = open(path, "w")  # noqa: WPS515
    try:
        yield handle        # the value bound by `as`
    finally:
        handle.close()
        print(f"  [close] Closed {path}")


@contextlib.contextmanager
def timer(label: str):
    """Measure the elapsed time of a code block."""
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        print(f"  [{label}] elapsed: {elapsed * 1000:.2f} ms")


def demo_function_context_manager(tmp_path: str = "/tmp/demo_output.txt"):
    print("\n" + "=" * 55)
    print("PART 2: Function-based context manager (@contextmanager)")
    print("=" * 55)

    print("\n--- File writer ---")
    # Flow for managed_file_writer:
    #   1. Generator runs to the `yield` → prints [open], opens file
    #   2. `yield handle` → binds handle to `f` in the with clause
    #   3. Body writes two records
    #   4. Body ends → generator resumes after yield → finally: closes file
    with managed_file_writer(tmp_path) as f:
        f.write("record 1\n")
        f.write("record 2\n")
        print(f"  [write] Wrote 2 records to {tmp_path}")

    print("\n--- Timer ---")
    # Flow for timer:
    #   1. Generator runs to yield → records start time
    #   2. Body does work
    #   3. finally block → computes elapsed → prints timing
    with timer("sort 1M items"):
        data = list(range(1_000_000, 0, -1))
        data.sort()
    print(f"  Sorted list length: {len(data)}")


# ══════════════════════════════════════════════════════════════════════════════
# PART 3: Suppressing exceptions inside __exit__
#
# Returning True from __exit__ tells Python: "I handled the exception;
# please discard it and continue execution after the with block."
#
# Returning False (or None) tells Python: "I didn't handle it;
# propagate the exception up the call stack as normal."
#
# Selective suppression pattern:
#   if exc_type is not None and issubclass(exc_type, <AllowedExceptions>):
#       return True   # suppress
#   return False      # propagate everything else
# ══════════════════════════════════════════════════════════════════════════════

class SuppressingContext:
    """A context manager that silently swallows a specific exception type.

    This is how contextlib.suppress() works internally — returning True
    from __exit__ signals Python to discard the exception.
    """

    def __init__(self, *exception_types):
        self._types = exception_types

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Flow when an exception occurred in the with body:
        #   exc_type is not None → there WAS an exception
        #   issubclass check  → is it one of the types we want to suppress?
        #   return True       → Python discards the exception, resumes after `with`
        #   return False      → Python re-raises the exception
        if exc_type is not None and issubclass(exc_type, self._types):
            print(f"  [suppress] Swallowed {exc_type.__name__}: {exc_val}")
            return True  # suppress — execution continues after the with block
        return False      # propagate any other exception


def demo_exception_suppression():
    print("\n" + "=" * 55)
    print("PART 3: Suppressing exceptions in __exit__")
    print("=" * 55)

    print("\n--- Suppress FileNotFoundError (expected during cleanup) ---")
    # Flow:
    #   1. __enter__ runs
    #   2. Body raises FileNotFoundError
    #   3. __exit__(FileNotFoundError, ...) → issubclass match → return True
    #   4. Python discards the exception → execution resumes AFTER the with block
    with SuppressingContext(FileNotFoundError):
        raise FileNotFoundError("temp file already deleted")
    print("  Execution resumed after the with block — exception was suppressed.")

    print("\n--- Do NOT suppress ValueError (unexpected) ---")
    # Flow:
    #   1. __enter__ runs
    #   2. Body raises ValueError
    #   3. __exit__(ValueError, ...) → issubclass check fails (not FileNotFoundError)
    #   4. return False → Python re-raises ValueError → outer try/except catches it
    try:
        with SuppressingContext(FileNotFoundError):
            raise ValueError("this is a real problem")
    except ValueError as e:
        print(f"  [propagated] ValueError: {e}")

    print("\nNote: contextlib.suppress() provides this same behaviour out of the box.")
    with contextlib.suppress(FileNotFoundError):
        raise FileNotFoundError("already gone")
    print("  contextlib.suppress worked the same way.")


def main():
    demo_class_context_manager()
    demo_function_context_manager()
    demo_exception_suppression()


if __name__ == "__main__":
    main()

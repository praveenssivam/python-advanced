"""
01_repr_and_eq.py
==================
Demonstrates Python's data model for object representation and equality:
  - The default (useless) repr and equality behaviour
  - Implementing __repr__ for readable output
  - Implementing __str__ for user-facing strings
  - Implementing __eq__ for value-based equality

Run:
    python module-02/01_repr_and_eq.py
"""


# ══════════════════════════════════════════════════════════════════════════════
# PART 1: Default repr and equality are often not useful
#
# Python's built-in fallbacks when you define no dunder methods:
#   repr(obj)  → "<ClassName object at 0x7f...>"  (memory address — useless)
#   str(obj)   → same as repr by default
#   obj1==obj2 → compares identity (is it the SAME object in memory?)
#                Two objects with identical data are never equal by default.
#
# The lesson: without __repr__ / __eq__ you cannot inspect or compare
# your objects meaningfully in logs, tests, or the REPL.
# ══════════════════════════════════════════════════════════════════════════════

class JobRunDefault:
    """No dunder methods — Python uses its built-in fallbacks for everything.

    repr  → memory address (changes every run, useless for debugging)
    str   → same as repr
    ==    → identity check (same object?), never True for two separate instances
    """

    def __init__(self, job_id: str, status: str, records: int):
        self.job_id = job_id
        self.status = status
        self.records = records


def demo_default_behaviour():
    print("=" * 55)
    print("PART 1: Default repr and equality")
    print("=" * 55)

    # Two separate objects — same data, but different locations in memory.
    run1 = JobRunDefault("job-101", "success", 4500)
    run2 = JobRunDefault("job-101", "success", 4500)

    # Flow: repr(run1)
    #   → Python looks for __repr__ on JobRunDefault → not found
    #   → falls back to object.__repr__ → returns "<...JobRunDefault at 0x…>"
    print(f"run1 repr  : {run1!r}")       # e.g. <__main__.JobRunDefault object at 0x...>
    print(f"run1 str   : {run1}")         # str() also falls back to __repr__

    # Flow: run1 == run2
    #   → Python looks for __eq__ on JobRunDefault → not found
    #   → falls back to object.__eq__ which checks  run1 is run2 (same id?)
    #   → they are different objects → False, even though all fields match
    print(f"run1 == run2: {run1 == run2}") # False — identity check, not value check
    print(f"run1 is run2: {run1 is run2}") # False — definitely different objects
    print()
    print("Two objects with identical data are not considered equal.")
    print("The repr tells us nothing useful about their state.")


# ══════════════════════════════════════════════════════════════════════════════
# PART 2: __repr__ and __str__
#
# Python's dispatch chain when you need a string representation:
#
#   repr(obj)   → calls obj.__repr__()              (always)
#   str(obj)    → calls obj.__str__()  if defined;
#                 falls back to __repr__() if not
#   print(obj)  → calls str(obj)  → follows the chain above
#   f"{obj}"   → calls str(obj)
#   f"{obj!r}" → calls repr(obj)  (the !r flag forces repr)
#   [obj, ...]  → uses repr for items inside containers
#
# __repr__: aimed at developers — unambiguous, ideally eval()-able.
#           Convention: ClassName(field1=..., field2=...)
# __str__ : aimed at end users — readable, can omit internal details.
#           If not defined, Python falls back to __repr__.
# ══════════════════════════════════════════════════════════════════════════════

class JobRun:
    """A pipeline job run result with all three dunder methods defined.

    __repr__: developer-facing — recreating the object from output is the goal.
    __str__ : user-facing — a concise one-liner suitable for logs or reports.
    __eq__  : value equality — two JobRuns with the same fields are equal.
    """

    def __init__(self, job_id: str, status: str, records: int):
        self.job_id = job_id
        self.status = status
        self.records = records

    def __repr__(self) -> str:
        # Convention: ClassName(field=value, ...) — unambiguous, ideally eval()-able.
        # Use !r on string fields so quotes are included in the output.
        return (
            f"JobRun(job_id={self.job_id!r}, "
            f"status={self.status!r}, "
            f"records={self.records})"
        )

    def __str__(self) -> str:
        # Human-readable summary — used by print(), str(), and f"{obj}".
        # Deliberately friendlier and less verbose than repr.
        return f"[{self.status.upper()}] Job {self.job_id} — {self.records:,} records processed"

    def __eq__(self, other: object) -> bool:
        # Accept `object` (not `JobRun`) so the type-checker is happy.
        # Return NotImplemented (not False) for unknown types — this tells Python
        # to try the OTHER operand's __eq__ before giving up. Returning False
        # would short-circuit that and break symmetry with other types.
        if not isinstance(other, JobRun):
            return NotImplemented
        return self.job_id == other.job_id and self.status == other.status and self.records == other.records


def demo_repr_and_str():
    print("\n" + "=" * 55)
    print("PART 2: __repr__ and __str__")
    print("=" * 55)

    run = JobRun("job-202", "success", 12_450)

    # Flow for each format expression:
    #   {run!r}  → repr(run) → JobRun.__repr__() → "JobRun(job_id='job-202', ...)"
    #   {run}    → str(run)  → JobRun.__str__()  → "[SUCCESS] Job job-202 — ..."
    #   {[run]}  → repr of list → repr() used for items inside containers
    print(f"repr : {run!r}")   # uses __repr__
    print(f"str  : {run}")     # uses __str__ (falls back to __repr__ if not defined)
    print(f"list : {[run]}")   # repr is used inside containers


# ══════════════════════════════════════════════════════════════════════════════
# PART 3: __eq__ for value-based equality
#
# Flow when Python evaluates  a == b :
#   1. Calls a.__eq__(b)
#   2. If that returns NotImplemented, Python calls b.__eq__(a) instead.
#   3. If both return NotImplemented, falls back to identity (a is b).
#
# Why return NotImplemented (not False) for unknown types?
#   Returning False would mean "these are definitely not equal", which is wrong
#   — you don't know what `b` is. NotImplemented says "I can't decide; let b
#   try". This preserves symmetry (a==b should behave the same as b==a).
#
# Side effect of __eq__: Python sets __hash__ = None, making the object
# unhashable by default. To restore hashability use frozen=True (@dataclass)
# or define __hash__ explicitly.
# ══════════════════════════════════════════════════════════════════════════════

class MetricPoint:
    """A timestamped measurement. Two points are equal if all three fields match.

    Demonstrates the correct signature: accept `object`, guard with isinstance,
    return NotImplemented for foreign types.
    """

    def __init__(self, metric: str, value: float, timestamp: str):
        self.metric = metric
        self.value = value
        self.timestamp = timestamp

    def __repr__(self) -> str:
        return f"MetricPoint({self.metric!r}, {self.value}, {self.timestamp!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MetricPoint):
            return NotImplemented  # let Python try the other side
        return (
            self.metric == other.metric
            and self.value == other.value
            and self.timestamp == other.timestamp
        )


def demo_eq():
    print("\n" + "=" * 55)
    print("PART 3: __eq__ for value-based equality")
    print("=" * 55)

    a = MetricPoint("cpu_pct", 72.5, "2026-03-01T10:00:00")
    b = MetricPoint("cpu_pct", 72.5, "2026-03-01T10:00:00")
    c = MetricPoint("cpu_pct", 90.0, "2026-03-01T10:00:00")

    print(f"a = {a!r}")
    print(f"b = {b!r}")
    print(f"c = {c!r}")
    print()
    print(f"a == b  (same data)      : {a == b}")   # True
    print(f"a == c  (different value): {a == c}")   # False
    print(f"a is b  (same object?)   : {a is b}")   # False — different objects
    print()

    # Equality enables use in sets and as dict keys (with __hash__ too)
    # Without __eq__, deduplication based on value would fail
    readings = [a, b, c]
    unique = []
    seen = []
    for r in readings:
        if r not in seen:
            seen.append(r)
            unique.append(r)
    print(f"De-duplicated readings: {unique}")
    print("a and b are collapsed into one because they are equal by value.")


# ══════════════════════════════════════════════════════════════════════════════
# PART 4: Quick comparison — before and after
# ══════════════════════════════════════════════════════════════════════════════

def demo_before_after():
    print("\n" + "=" * 55)
    print("PART 4: Before / After summary")
    print("=" * 55)

    # BEFORE: no __repr__ or __eq__
    # Flow: repr(bad) → object.__repr__ → memory address
    # Flow: bad == JobRunDefault(...) → object.__eq__ → identity check → False
    bad = JobRunDefault("job-303", "failed", 0)
    print(f"Before __repr__/__eq__:")
    print(f"  repr : {bad!r}")  # useless memory address
    print(f"  equal to itself by value? {bad == JobRunDefault('job-303', 'failed', 0)}")  # False!

    # AFTER: all three dunders defined
    # Flow: repr(good) → JobRun.__repr__ → readable class-name+fields string
    # Flow: good == JobRun(...) → JobRun.__eq__ → field-by-field comparison → True
    good = JobRun("job-303", "failed", 0)
    print(f"\nAfter __repr__/__eq__:")
    print(f"  repr : {good!r}")   # readable
    print(f"  str  : {good}")     # user-friendly
    print(f"  equal to itself by value? {good == JobRun('job-303', 'failed', 0)}")  # True

    # Demonstrate that __repr__ output is eval()-able (a best practice)
    print("\nTesting that __repr__ output can be eval()-ed back to an equal object:")
    good_repr = "JobRun('job-303', 'failed', 0)"
    print(f"\n  repr output: {good_repr}")
    reconstructed = eval(good_repr)
    print(f"  reconstructed object: {reconstructed!r}")
    print(f"  reconstructed object is equal to original? {reconstructed == good}")


def main():
    demo_default_behaviour()
    demo_repr_and_str()
    demo_eq()
    demo_before_after()


if __name__ == "__main__":
    main()

"""
core/models.py — Domain models for Validify.

─────────────────────────────────────────────────────────
DAY 1 TASK
─────────────────────────────────────────────────────────
Implement ValidationResult as a plain class (not a dataclass yet):

    class ValidationResult:
        def __init__(self, field, rule, passed, message):
            ...

Fields:
  field   (str)  — the CSV column name that was checked
  rule    (str)  — the rule class name (e.g. "NullCheckRule")
  passed  (bool) — True if the check succeeded
  message (str)  — human-readable description of the failure ("" if passed)

─────────────────────────────────────────────────────────
DAY 2 TASK
─────────────────────────────────────────────────────────
1. Convert ValidationResult to @dataclass.
   Add __repr__ (automatic with dataclass) and confirm __eq__ works.

2. Add DataRecord dataclass:
      row_number : int
      fields     : dict[str, str]

3. Add Report dataclass:
      total   : int
      passed  : int
      failed  : int
      results : list[ValidationResult]   ← use field(default_factory=list)

   Add a @property:
      pass_rate -> float   (0.0 to 100.0, rounded to 1 decimal)

Hint: import dataclass and field from the dataclasses module.
"""

"""
core/models.py — Domain models for Validify.

─────────────────────────────────────────────────────────
Day 1 implementation notes
─────────────────────────────────────────────────────────
ValidationResult is implemented as a plain Python class here, not a dataclass.

Reason: writing __init__, __repr__, and __eq__ by hand first makes it
immediately obvious what @dataclass automates on Day 2. The before/after
contrast is the whole point — seeing the boilerplate disappear gives the
abstraction real meaning rather than being just a decorator you copy-paste.

Day 2: ValidationResult is converted to @dataclass, and DataRecord + Report
are added.
─────────────────────────────────────────────────────────
"""

from dataclasses import dataclass, field  # noqa: F401 — used on Day 2


# ───────────────────────────────────────────────────────────────────────────────
# DAY 1 — ValidationResult as a plain class
# ───────────────────────────────────────────────────────────────────────────────


class ValidationResult:
    """Holds the outcome of a single rule applied to a single record.

    This is a VALUE OBJECT — it is created once, never mutated, and passed
    around for reporting.

    On Day 2, @dataclass will generate __init__, __repr__, and __eq__
    automatically. Writing them by hand here first makes it clear exactly
    what the decorator eliminates.
    """

    def __init__(self, field: str, rule: str, passed: bool, message: str) -> None:
        # __init__ initialises an already-created object (self); it is not a
        # constructor that returns a new instance. Assignments go to self.<name>.
        self.field = field
        self.rule = rule
        self.passed = passed
        self.message = message

    def __repr__(self) -> str:
        # __repr__ is what Python prints when you inspect the object in a REPL.
        # Convention: make it look like the expression that would recreate it.
        status = "PASS" if self.passed else "FAIL"
        return (
            f"ValidationResult(field={self.field!r}, rule={self.rule!r}, "
            f"status={status!r}, message={self.message!r})"
        )


# ───────────────────────────────────────────────────────────────────────────────
# DAY 2 stubs — implement these after converting ValidationResult to @dataclass
# ───────────────────────────────────────────────────────────────────────────────

# TODO Day 2: convert ValidationResult to @dataclass
# TODO Day 2: add DataRecord dataclass
# TODO Day 2: add Report dataclass with @property pass_rate

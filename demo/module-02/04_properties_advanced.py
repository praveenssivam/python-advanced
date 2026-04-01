"""
04_properties_advanced.py
===========================
Demonstrates advanced property usage:
  - A computed (read-only) property derived from stored state
  - A validated property setter that rejects bad values
  - Separating the stored internal value from the presented value
  - Using __post_init__ with dataclasses for validation

Run:
    python module-02/04_properties_advanced.py
"""

from dataclasses import dataclass, field


# ══════════════════════════════════════════════════════════════════════════════
# PART 1: Computed property — derived from stored state
#
# A computed property has a getter but NO setter.
# The value is derived from one or more stored fields every time it is accessed.
#
# Why use a computed property instead of a stored field?
#   If you store duration separately you have THREE pieces of state that must
#   always be consistent: start, end, duration. Any mutation to start or end
#   requires remembering to update duration too — easy to miss.
#   A computed property collapses that to TWO authoritative fields (start, end)
#   and derives everything else on demand. Stale state is impossible.
#
# Flow when you access  w.duration_sec :
#   1. Python calls DataWindow.duration_sec.fget(w)
#   2. Returns self._end - self._start  — always fresh
#
# Flow when you try to SET  w.duration_sec = 100 :
#   1. Python looks for a setter on the property
#   2. None exists → raises AttributeError immediately
# ══════════════════════════════════════════════════════════════════════════════

class DataWindow:
    """A time-bounded data window. Duration is always derived from its boundaries.

    Authoritative state : _start, _end  (set once in __init__, validated)
    Computed properties : duration_sec, duration_min  (derived, no setter)
    Read-only accessors : start, end  (expose private fields without a setter)

    Design choice: storing duration separately would risk drift. Computing it
    on demand guarantees start + end + duration are always consistent.
    """

    def __init__(self, start_ts: float, end_ts: float):
        # Validate first — store directly to private names (no setters for start/end).
        # DataWindow is intentionally immutable once created.
        if end_ts <= start_ts:
            raise ValueError(f"end_ts must be after start_ts (got {start_ts}, {end_ts})")
        self._start = start_ts
        self._end = end_ts

    @property
    def start(self) -> float:
        """Read-only access to the window start timestamp."""
        return self._start

    @property
    def end(self) -> float:
        """Read-only access to the window end timestamp."""
        return self._end

    @property
    def duration_sec(self) -> float:
        """Computed — always consistent with start and end. No risk of stale state.

        No setter exists. Attempting  w.duration_sec = x  raises AttributeError.
        """
        return self._end - self._start

    @property
    def duration_min(self) -> float:
        """Delegates to duration_sec — chaining computed properties is fine."""
        return self.duration_sec / 60

    def __repr__(self) -> str:
        return f"DataWindow(start={self._start}, end={self._end}, duration={self.duration_sec}s)"


def demo_computed_property():
    print("=" * 55)
    print("PART 1: Computed property")
    print("=" * 55)

    # Flow: DataWindow(1_000_000.0, 1_003_600.0)
    #   → __init__ validates end_ts > start_ts ✓
    #   → stores self._start = 1_000_000.0, self._end = 1_003_600.0
    w = DataWindow(start_ts=1_000_000.0, end_ts=1_003_600.0)
    print(f"Window   : {w!r}")

    # Flow: w.duration_sec
    #   → Python calls DataWindow.duration_sec.fget(w)
    #   → returns self._end - self._start = 3600.0
    # Flow: w.duration_min
    #   → calls duration_sec first → 3600.0 / 60 = 60.0
    print(f"Duration : {w.duration_sec:.0f} seconds = {w.duration_min:.1f} minutes")
    print()

    # Flow: w.duration_sec = 100
    #   → Python looks for @duration_sec.setter → none defined
    #   → raises AttributeError immediately
    try:
        w.duration_sec = 100  # type: ignore
    except AttributeError as e:
        print(f"Cannot set computed property: {e}")

    print()
    print("The duration is always consistent with start and end.")
    print("There is no stored duration field that could go out of sync.")


# ══════════════════════════════════════════════════════════════════════════════
# PART 2: Validation setter — reject bad values before storing
#
# Pattern: expose a public name (hz) backed by a private store (_hz).
# ALL writes — including the one inside __init__ — go through the setter,
# so the object can never hold an invalid value.
#
# Flow when you write  sr.hz = value :
#   1. Python intercepts the assignment and calls @hz.setter(value)
#   2. Setter checks type  → raises TypeError if not int
#   3. Setter checks range → raises ValueError if outside [MIN_HZ, MAX_HZ]
#   4. Only if both checks pass, the value is stored in self._hz
#   5. period_ms is a computed property: it always reads self._hz, so it
#      can never be out of sync with the current hz value.
# ══════════════════════════════════════════════════════════════════════════════

class SamplingRate:
    """Encapsulates a data sampling rate in Hz with range validation.

    Public interface : sr.hz       — read or write (validated)
                       sr.period_ms — read-only, always derived from hz

    Internal storage : self._hz    — only ever written by the setter,
                                     so it is always a valid integer in range.
    """

    MIN_HZ = 1        # lower bound — 1 Hz minimum meaningful rate
    MAX_HZ = 10_000   # upper bound — 10 kHz hardware ceiling

    def __init__(self, hz: int):
        # IMPORTANT: assign to self.hz (public name), NOT self._hz directly.
        # This routes the initial value through the setter so validation
        # fires at construction time, not just on later mutations.
        self.hz = hz

    @property
    def hz(self) -> int:
        """Read access — returns the validated private backing store."""
        return self._hz

    @hz.setter
    def hz(self, value: int) -> None:
        """Write access — validates before storing.

        Step 1: type guard — only plain ints accepted (bool is a subclass of
                int in Python, but floats like 3.5 are not).
        Step 2: range guard — must be within [MIN_HZ, MAX_HZ].
        Step 3: store — only reached if both guards pass.
        """
        if not isinstance(value, int):
            raise TypeError(f"hz must be an int, got {type(value).__name__}")
        if not (self.MIN_HZ <= value <= self.MAX_HZ):
            raise ValueError(f"hz must be in [{self.MIN_HZ}, {self.MAX_HZ}], got {value}")
        self._hz = value  # safe to store — all checks passed

    @property
    def period_ms(self) -> float:
        """Computed from hz — always synchronised, never stale.

        Because _hz is only ever written through the validated setter,
        this calculation is always safe (no division-by-zero risk since
        hz >= 1 is enforced).
        """
        return 1000 / self._hz

    def __repr__(self) -> str:
        return f"SamplingRate(hz={self._hz}, period={self.period_ms:.3f} ms)"


def demo_validation_setter():
    print("\n" + "=" * 55)
    print("PART 2: Validation setter")
    print("=" * 55)

    # Flow: SamplingRate(100)
    #   → __init__ runs  self.hz = 100
    #   → setter fires   isinstance(100, int) ✓   1 <= 100 <= 10000 ✓
    #   → self._hz = 100
    sr = SamplingRate(100)
    print(f"Initial: {sr!r}")

    # Flow: sr.hz = 1000
    #   → setter fires   isinstance(1000, int) ✓   1 <= 1000 <= 10000 ✓
    #   → self._hz updated to 1000
    #   → period_ms now reflects: 1000 / 1000 = 1.000 ms
    sr.hz = 1000
    print(f"After   hz=1000: {sr!r}")

    print("\nRejection cases:")
    for bad in [-1, 0, 20_000, 3.5, "fast"]:
        # Flow for each bad value:
        #   → setter fires   check fails (range or type)
        #   → exception raised BEFORE self._hz is touched
        #   → sr._hz remains 1000 — object state is unchanged
        try:
            sr.hz = bad  # type: ignore
        except (ValueError, TypeError) as e:
            print(f"  Rejected {bad!r}: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# PART 3: Stored value vs. presented value
#
# Pattern: normalise input at write-time so every consumer reads clean data.
# Store the canonical form internally; derive display forms via properties.
#
# Flow when you write  col.name = "  TRIP_DISTANCE  " :
#   1. Python calls the @name.setter
#   2. Setter strips whitespace and lower-cases → "trip_distance"
#   3. Stores self._name = "trip_distance"
#
# Flow when you access  col.display_name :
#   1. Python calls the @display_name getter
#   2. Takes the already-canonical _name, replaces _ with space, title-cases
#   3. Returns "Trip Distance"  — derived on demand from the clean internal form
#
# Advantage: normalisation happens ONCE (at set-time). Every subsequent read
# of any property sees clean, consistent data — no matter how messy the input.
# ══════════════════════════════════════════════════════════════════════════════

class ColumnSpec:
    """A table column specification.

    Canonical (stored) form : lowercase, stripped — e.g. "trip_distance"
    Presented form          : title-cased via display_name property
    dtype                   : normalised to lowercase at set-time

    Consumers always receive clean data regardless of how messy the input was.
    """

    ALLOWED_TYPES = {"integer", "float", "string", "boolean", "timestamp"}

    def __init__(self, name: str, dtype: str, nullable: bool = True):
        # Route through setters so normalisation/validation fires at construction.
        # Writing to self.name (not self._name) calls the setter.
        self.name = name    # setter strips + lower-cases
        self.dtype = dtype  # setter validates against ALLOWED_TYPES
        self.nullable = nullable  # plain bool — no setter needed

    @property
    def name(self) -> str:
        """Canonical (lowercase, stripped) column name."""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        """Normalise at write-time: strip whitespace and lower-case.

        Rejects blank or whitespace-only names immediately.
        """
        if not value or not value.strip():
            raise ValueError("Column name cannot be empty")
        self._name = value.strip().lower()  # canonical form stored here

    @property
    def display_name(self) -> str:
        """Presented form — title-cased version of the canonical name.

        Derived on demand from _name. No separate storage needed.
        """
        return self._name.replace("_", " ").title()

    @property
    def dtype(self) -> str:
        """Normalised (lowercase) data type string."""
        return self._dtype

    @dtype.setter
    def dtype(self, value: str) -> None:
        """Normalise and validate the data type at write-time.

        Strips + lower-cases before checking against ALLOWED_TYPES so
        inputs like "Float" or " INTEGER " are accepted.
        """
        normalised = value.strip().lower()
        if normalised not in self.ALLOWED_TYPES:
            raise ValueError(f"Unknown dtype {value!r}. Allowed: {sorted(self.ALLOWED_TYPES)}")
        self._dtype = normalised  # store normalised form

    def __repr__(self) -> str:
        nullable_str = "nullable" if self.nullable else "not null"
        return f"ColumnSpec({self._name!r}: {self._dtype}, {nullable_str})"


def demo_stored_vs_presented():
    print("\n" + "=" * 55)
    print("PART 3: Stored value vs. presented value")
    print("=" * 55)

    # Messy input: extra whitespace + wrong case
    # Flow: ColumnSpec("  TRIP_DISTANCE  ", "Float")
    #   → __init__ runs  self.name = "  TRIP_DISTANCE  "
    #   → @name.setter   strips + lowers → self._name = "trip_distance"
    #   → __init__ runs  self.dtype = "Float"
    #   → @dtype.setter  normalises → "float", validates ✓ → self._dtype = "float"
    col = ColumnSpec("  TRIP_DISTANCE  ", "Float")

    # Flow: col.name        →  getter returns self._name = 'trip_distance'
    # Flow: col.display_name →  derived: 'trip_distance' → 'Trip Distance'
    # Flow: col.dtype        →  getter returns self._dtype = 'float'
    print(f"Stored  name : {col.name!r}")          # canonical form
    print(f"Display name : {col.display_name!r}")  # presented form
    print(f"Stored  dtype: {col.dtype!r}")         # normalised
    print(f"repr         : {col!r}")
    print()
    print("Input was normalised at set-time — consumers always get clean data.")

    # Flow: col.dtype = "blob"
    #   → @dtype.setter  normalises → "blob", not in ALLOWED_TYPES → ValueError
    #   → self._dtype is unchanged — object state is intact
    try:
        col.dtype = "blob"
    except ValueError as e:
        print(f"\nRejected bad dtype: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# PART 4: Properties in a dataclass via __post_init__
#
# @dataclass generates __init__ automatically, so there is no place to put
# constructor-time validation... unless you use __post_init__.
#
# Flow when you instantiate a @dataclass:
#   1. The generated __init__ runs — assigns every field in order.
#   2. If __post_init__ is defined, the generated __init__ calls it last.
#   3. __post_init__ can read all fields and raise if invariants are violated.
#   4. If it raises, the object is never returned to the caller.
#
# This is the idiomatic way to validate multi-field constraints inside a
# dataclass (e.g. "these three percentages must sum to 100").
# A @property on a dataclass works exactly the same as on a regular class.
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class BudgetAllocation:
    """Budget split across named categories. Validates that percentages sum to 100.

    @dataclass generates __init__ and __repr__.
    __post_init__ runs after __init__ to enforce the 100% invariant.
    largest_category is a computed @property — no stored value that can drift.
    """
    name: str
    allocations: dict[str, float]  # category → percentage (must sum to 100)

    def __post_init__(self) -> None:
        """Called automatically by the generated __init__ after all fields are set.

        Flow:
          1. Generated __init__ sets self.name and self.allocations.
          2. Generated __init__ calls self.__post_init__().
          3. We sum the allocation values and raise if they don't sum to ~100.
        """
        total = sum(self.allocations.values())
        if abs(total - 100.0) > 0.01:
            raise ValueError(
                f"Allocations must sum to 100.0, got {total:.2f} for '{self.name}'"
            )

    @property
    def largest_category(self) -> str:
        """Computed on demand — finds the category with the highest allocation."""
        return max(self.allocations, key=self.allocations.__getitem__)


def demo_post_init():
    print("\n" + "=" * 55)
    print("PART 4: __post_init__ validation in a dataclass")
    print("=" * 55)

    # Flow: BudgetAllocation("Q1", {...})
    #   1. Generated __init__ sets self.name = "Q1", self.allocations = {...}
    #   2. Generated __init__ calls self.__post_init__()
    #   3. __post_init__ sums values: 45 + 30 + 25 = 100.0 ✓ → no error
    #   4. Object is returned to caller
    b = BudgetAllocation("Q1", {"compute": 45.0, "storage": 30.0, "networking": 25.0})
    print(f"Budget: {b!r}")

    # Flow: b.largest_category
    #   → @property getter runs max(...) over allocations dict → "compute"
    print(f"Largest category: {b.largest_category}")

    # Flow: BudgetAllocation("Q2", {"compute": 60.0, "storage": 20.0})
    #   1. Generated __init__ sets both fields
    #   2. Calls __post_init__: sum = 80.0, abs(80 - 100) = 20 > 0.01 → ValueError
    #   3. Exception propagates — the half-constructed object is discarded
    try:
        BudgetAllocation("Q2", {"compute": 60.0, "storage": 20.0})
    except ValueError as e:
        print(f"Invalid budget: {e}")


def main():
    demo_computed_property()
    demo_validation_setter()
    demo_stored_vs_presented()
    demo_post_init()


if __name__ == "__main__":
    main()

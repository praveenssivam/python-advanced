"""
09_functional_vs_oop.py
========================
The same data-cleaning problem solved three ways:

  1. OOP      — a class that holds state and exposes methods
  2. Functional — stateless pure functions + closures for configuration
  3. Hybrid    — a @dataclass for data + standalone pure functions for logic

None is universally "best". The point is to understand when each style
makes code easier to read, test, and extend.

Run:
    python demo/module-04/09_functional_vs_oop.py
"""

from dataclasses import dataclass, field
from functools import reduce
from typing import Callable


# ─────────────────────────────────────────────────────────────────────────────
# Shared data used by all three styles
# ─────────────────────────────────────────────────────────────────────────────

RAW_RECORDS = [
    {"trip_id": "T01", "distance": "  4.2 ", "fare": "12.50",  "status": None},
    {"trip_id": "T02", "distance": "abc",    "fare": "8.00",   "status": "cancelled"},
    {"trip_id": "T03", "distance": "1.1",    "fare": " 5.5 ",  "status": None},
    {"trip_id": "T04", "distance": "9.9",    "fare": "-3.00",  "status": None},
    {"trip_id": "T05", "distance": "3.3",    "fare": "14.00",  "status": None},
]


# ══════════════════════════════════════════════════════════════════════════════
# STYLE 1 — OOP: DataCleaner class
#
# State and behaviour bundled together.
# Configuration stored as instance attributes in __init__.
# Methods operate on self._records (mutable list).
#
# Advantages:
#   + Groups related operations under one namespace
#   + Easy to persist configuration (min_fare, excluded)
#   + Familiar to developers coming from Java / C#
#
# Disadvantages:
#   - Mutable state → calling methods in different order gives different results
#   - Harder to test individual transforms in isolation
#   - Subclassing for variations can lead to deep hierarchies
# ══════════════════════════════════════════════════════════════════════════════

class DataCleaner:
    """Clean and validate a list of trip records.

    Public interface:
        cleaner = DataCleaner(records, min_fare=5.0)
        cleaner.strip_string_fields()
        cleaner.filter_cancelled()
        cleaner.parse_numerics()
        cleaner.filter_invalid_fare()
        result = cleaner.records       ← cleaned records

    Internal state:
        self._records  — mutable list, updated in place by each method
        self._min_fare — minimum acceptable fare
    """

    def __init__(self, records: list, min_fare: float = 0.0):
        # Flow: DataCleaner(records, min_fare=5.0)
        #   → self._records = deepcopy(records)   (don't mutate caller's data)
        #   → self._min_fare = 5.0
        self._records = [dict(r) for r in records]   # shallow copy each row
        self._min_fare = min_fare

    @property
    def records(self) -> list:
        return self._records

    def strip_string_fields(self) -> "DataCleaner":
        """Strip whitespace from all string values."""
        for row in self._records:
            for k, v in row.items():
                if isinstance(v, str):
                    row[k] = v.strip()
        return self   # fluent API — allows chaining

    def filter_cancelled(self) -> "DataCleaner":
        """Remove rows where status == 'cancelled'."""
        self._records = [r for r in self._records if r.get("status") != "cancelled"]
        return self

    def parse_numerics(self) -> "DataCleaner":
        """Convert distance and fare to float; remove rows where conversion fails."""
        cleaned = []
        for row in self._records:
            try:
                row["distance"] = float(row["distance"])
                row["fare"]     = float(row["fare"])
                cleaned.append(row)
            except (ValueError, TypeError):
                pass
        self._records = cleaned
        return self

    def filter_invalid_fare(self) -> "DataCleaner":
        """Remove rows with fare below min_fare."""
        self._records = [r for r in self._records if r["fare"] >= self._min_fare]
        return self


def demo_oop_style():
    print("=" * 55)
    print("STYLE 1 — OOP: DataCleaner class (fluent API)")
    print("=" * 55)
    print()

    # Flow: DataCleaner → strip → filter_cancelled → parse → filter_fare
    result = (
        DataCleaner(RAW_RECORDS, min_fare=5.0)
        .strip_string_fields()
        .filter_cancelled()
        .parse_numerics()
        .filter_invalid_fare()
        .records
    )

    print(f"  Input rows:  {len(RAW_RECORDS)}")
    print(f"  Output rows: {len(result)}")
    for row in result:
        print(f"    {row}")


# ══════════════════════════════════════════════════════════════════════════════
# STYLE 2 — Functional: pure functions + closures
#
# No class, no shared state.
# Each function takes a list/record and returns a NEW list/record.
# Configuration is captured via closures (make_fare_filter) or defaults.
#
# Advantages:
#   + Each function is independently testable
#   + No hidden state → calling order is explicit in the pipeline
#   + Easy to swap or reorder transforms
#
# Disadvantages:
#   - Configuration must be passed explicitly (or captured in closures)
#   - Less familiar to class-oriented developers
# ══════════════════════════════════════════════════════════════════════════════

def strip_fields(records: list) -> list:
    """Return new list with all string field values stripped."""
    return [
        {k: v.strip() if isinstance(v, str) else v for k, v in row.items()}
        for row in records
    ]


def remove_cancelled(records: list) -> list:
    """Return new list excluding cancelled rows."""
    return [r for r in records if r.get("status") != "cancelled"]


def parse_numeric_fields(records: list) -> list:
    """Return new list with distance and fare parsed as float; drop bad rows."""
    result = []
    for row in records:
        try:
            result.append({**row, "distance": float(row["distance"]),
                                  "fare":     float(row["fare"])})
        except (ValueError, TypeError):
            pass
    return result


def make_fare_filter(min_fare: float) -> Callable:
    """Return a filter function that keeps rows with fare >= min_fare.

    Flow: make_fare_filter(5.0) → closure(records)
      where closure captures min_fare=5.0 in its __closure__.
    """
    def fare_filter(records: list) -> list:
        return [r for r in records if r["fare"] >= min_fare]
    return fare_filter


def run_pipeline(records: list, transforms: list) -> list:
    """Apply each transform in order, threading the result through.

    Flow: reduce(apply_transform, transforms, initial=records)
      step 1: records → strip_fields(records)
      step 2: result1 → remove_cancelled(result1)
      ...
    """
    return reduce(lambda data, fn: fn(data), transforms, records)


def demo_functional_style():
    print("\n" + "=" * 55)
    print("STYLE 2 — Functional: pure functions + pipeline")
    print("=" * 55)
    print()

    # Build the pipeline — closures make configuration injectable
    pipeline = [
        strip_fields,
        remove_cancelled,
        parse_numeric_fields,
        make_fare_filter(min_fare=5.0),
    ]

    # Flow: RAW_RECORDS → strip → remove_cancelled → parse → fare_filter
    result = run_pipeline(RAW_RECORDS, pipeline)

    print(f"  Input rows:  {len(RAW_RECORDS)}")
    print(f"  Output rows: {len(result)}")
    for row in result:
        print(f"    {row}")

    print()
    print("  Reusing individual steps for a lighter pipeline (no fare filter):")
    mini_result = run_pipeline(RAW_RECORDS, [strip_fields, parse_numeric_fields])
    print(f"  Mini-pipeline rows: {len(mini_result)}")


# ══════════════════════════════════════════════════════════════════════════════
# STYLE 3 — Hybrid: @dataclass for data + functions for logic
#
# @dataclass handles __init__, __repr__, __eq__ boilerplate automatically.
# Logic lives in standalone functions that operate on dataclass instances.
#
# This separates DATA (what a trip is) from BEHAVIOUR (how to clean trips).
# The dataclass is intentionally simple — it IS the data.
#
# Advantages:
#   + Data structure is explicit and self-documenting
#   + Logic functions are pure and independently testable
#   + __eq__ works out of the box (useful in tests)
#
# Pattern: the dataclass acts as a typed, validated container;
#          functions act as transformations on those containers.
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class TripRecord:
    """Parsed and validated trip record.

    Fields default to None to indicate 'not yet validated'.
    """
    trip_id:  str
    distance: float | None = None
    fare:     float | None = None
    status:   str | None   = None
    valid:    bool          = False


def parse_record(raw: dict) -> TripRecord | None:
    """Try to build a TripRecord from a raw dict; return None if invalid.

    Flow: raw dict → TripRecord(trip_id, distance=float(raw.distance), ...)
                   → None if distance/fare cannot be parsed
    """
    if raw.get("status") == "cancelled":
        return None
    try:
        return TripRecord(
            trip_id  = raw["trip_id"],
            distance = float(str(raw.get("distance", "")).strip()),
            fare     = float(str(raw.get("fare", "")).strip()),
            status   = raw.get("status"),
        )
    except (ValueError, TypeError):
        return None


def validate_record(record: TripRecord, min_fare: float = 5.0) -> TripRecord:
    """Return a new TripRecord with valid=True if fare meets the threshold.

    Flow: record → if record.fare >= min_fare → TripRecord(**record, valid=True)
    """
    from dataclasses import replace
    return replace(record, valid=record.fare is not None and record.fare >= min_fare)


def demo_hybrid_style():
    print("\n" + "=" * 55)
    print("STYLE 3 — Hybrid: @dataclass + pure functions")
    print("=" * 55)
    print()

    parsed   = [parse_record(r) for r in RAW_RECORDS]
    parsed   = [r for r in parsed if r is not None]      # drop None (bad/cancelled)
    validated = [validate_record(r, min_fare=5.0) for r in parsed]
    result    = [r for r in validated if r.valid]

    print(f"  Input rows:  {len(RAW_RECORDS)}")
    print(f"  Parsed rows: {len(parsed)}  (dropped bad/cancelled)")
    print(f"  Output rows: {len(result)}")
    for row in result:
        print(f"    {row}")


# ══════════════════════════════════════════════════════════════════════════════
# Summary comparison
# ══════════════════════════════════════════════════════════════════════════════

def print_comparison():
    print("\n" + "=" * 55)
    print("COMPARISON")
    print("=" * 55)
    comparison = """
  Style       | State      | Testability | Familiar to    | Best for
  ─────────────┼────────────┼─────────────┼────────────────┼──────────────────
  OOP class   | mutable    | medium      | Java / C# devs | Stateful services
  Functional  | none       | high        | FP learners    | Pure transforms
  Hybrid      | in data    | high        | all            | Typed pipelines
"""
    print(comparison)


def main():
    demo_oop_style()
    demo_functional_style()
    demo_hybrid_style()
    print_comparison()


if __name__ == "__main__":
    main()

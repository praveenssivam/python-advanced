"""
07_immutability.py
===================
Immutability means "never modify an object in place — produce a new one".

Python does not enforce immutability on dicts or lists, but the functional
programming style TREATS them as immutable by convention:

  - Instead of dict["key"] = value     → use {**dict, "key": value}
  - Instead of list.append(item)       → use [*list, item]
  - Instead of list.remove(item)       → use [x for x in list if x != item]

Why bother?
  - Easier to reason about: a function cannot mutate its caller's data.
  - Safer for concurrent code: no shared mutable state.
  - Simpler tests: inputs before and after a function are independent.

Run:
    python demo/module-04/07_immutability.py
"""

from copy import deepcopy
from typing import Any


# ══════════════════════════════════════════════════════════════════════════════
# PART 1: Mutable vs immutable dict update
#
# Mutable approach:
#   record["status"] = "validated"    ← modifies the original dict
#   caller's variable now sees a CHANGED dict — surprising and hard to trace
#
# Immutable approach:
#   new_record = {**record, "status": "validated"}
#   ← creates a NEW dict; original record is NOT touched
#   caller's variable still sees the original — no surprise
# ══════════════════════════════════════════════════════════════════════════════

def enrich_mutable(record: dict, key: str, value: Any) -> dict:
    """BAD: modifies the original dict in place and returns it."""
    record[key] = value          # ← mutation!
    return record


def enrich_immutable(record: dict, key: str, value: Any) -> dict:
    """GOOD: returns a new dict; original is unchanged.

    Flow: {**record} copies every key-value pair into a new dict object,
          then the trailing key=value overrides or adds that field.
    """
    return {**record, key: value}   # ← new dict, original untouched


def demo_dict_update():
    print("=" * 55)
    print("PART 1: Mutable vs immutable dict update")
    print("=" * 55)
    print()

    original = {"trip_id": "A1", "distance": 4.2, "status": "raw"}

    print(f"  Original: {original}")
    print()

    # Mutable
    copy_for_mutable = dict(original)   # shallow copy so we can compare
    result_mutable = enrich_mutable(copy_for_mutable, "status", "validated")
    print("  Mutable approach (enrich_mutable):")
    print(f"    After call:  result    = {result_mutable}")
    print(f"    After call:  original? = {copy_for_mutable}")
    print(f"    same object? {result_mutable is copy_for_mutable}  ← mutated in-place")

    print()

    # Immutable
    result_immutable = enrich_immutable(original, "status", "validated")
    print("  Immutable approach (enrich_immutable):")
    print(f"    After call:  result    = {result_immutable}")
    print(f"    After call:  original  = {original}")
    print(f"    same object? {result_immutable is original}  ← original untouched")


# ══════════════════════════════════════════════════════════════════════════════
# PART 2: Mutable vs immutable list operations
#
# Mutable:   results.append(row)         ← changes results in place
# Immutable: results = [*results, row]   ← new list, old one unchanged
#
# Mutable filter: list.remove(item), del list[i]
# Immutable filter: [x for x in items if condition(x)]
# ══════════════════════════════════════════════════════════════════════════════

def add_row_mutable(rows: list, new_row: dict) -> list:
    """BAD: appends to the original list and returns it."""
    rows.append(new_row)    # ← mutation of caller's list!
    return rows


def add_row_immutable(rows: list, new_row: dict) -> list:
    """GOOD: returns a new list with new_row appended.

    [*rows, new_row] unpacks all items from rows into a new list
    and then appends new_row at the end.
    """
    return [*rows, new_row]


def filter_mutable(rows: list, key: str, value: Any) -> list:
    """BAD: removes items in place by rebuilding the list using slice assignment."""
    rows[:] = [r for r in rows if r.get(key) != value]    # ← in-place mutation
    return rows


def filter_immutable(rows: list, key: str, value: Any) -> list:
    """GOOD: returns a new filtered list; original is unchanged."""
    return [r for r in rows if r.get(key) != value]


def demo_list_operations():
    print("\n" + "=" * 55)
    print("PART 2: Mutable vs immutable list operations")
    print("=" * 55)
    print()

    base_rows = [
        {"trip_id": "A1", "valid": True},
        {"trip_id": "A2", "valid": False},
        {"trip_id": "A3", "valid": True},
    ]
    new_row = {"trip_id": "A4", "valid": True}

    # -- add row --
    mutable_list = list(base_rows)   # shallow copy to preserve base
    result_m = add_row_mutable(mutable_list, new_row)
    immutable_list = list(base_rows)
    result_i = add_row_immutable(immutable_list, new_row)

    print("  add_row_mutable:")
    print(f"    caller's list length after call: {len(mutable_list)}  (was 3)")
    print(f"    same list object returned?       {result_m is mutable_list}")
    print()
    print("  add_row_immutable:")
    print(f"    caller's list length after call: {len(immutable_list)}  (still 3 → unchanged)")
    print(f"    same list object returned?       {result_i is immutable_list}")

    print()

    # -- filter --
    rows_for_filter = list(base_rows)
    filtered_immutable = filter_immutable(rows_for_filter, "valid", False)
    print("  filter_immutable (keep valid=True rows):")
    print(f"    original rows count: {len(rows_for_filter)}  (unchanged)")
    print(f"    filtered rows count: {len(filtered_immutable)}")
    print(f"    filtered rows: {[r['trip_id'] for r in filtered_immutable]}")


# ══════════════════════════════════════════════════════════════════════════════
# PART 3: Pure transformation pipeline using immutable updates
#
# Each transform function receives a record and returns a NEW record
# with the update applied.  They can be composed into a pipeline.
#
# Flow for process(record):
#   1. tag_source(record)   → {**record, "source": "taxi_feed"}
#   2. add_tax(record)      → {**record, "tax": record["fare"] * 0.1}
#   3. round_values(record) → {**record with floats rounded to 2 dp}
# ══════════════════════════════════════════════════════════════════════════════

def tag_source(record: dict, source: str = "taxi_feed") -> dict:
    return {**record, "source": source}


def add_tax(record: dict, rate: float = 0.10) -> dict:
    fare = record.get("fare", 0.0)
    return {**record, "tax": round(fare * rate, 2), "total": round(fare * (1 + rate), 2)}


def round_values(record: dict, precision: int = 2) -> dict:
    """Return a new record with all float values rounded to `precision` places."""
    return {
        k: round(v, precision) if isinstance(v, float) else v
        for k, v in record.items()
    }


def demo_immutable_pipeline():
    print("\n" + "=" * 55)
    print("PART 3: Pure transformation pipeline")
    print("=" * 55)
    print()

    raw = {"trip_id": "T99", "distance": 4.2551, "fare": 12.3456}
    print(f"  Input:  {raw}")

    step1 = tag_source(raw)
    step2 = add_tax(step1)
    step3 = round_values(step2)

    print(f"  Step 1 tag_source:   {step1}")
    print(f"  Step 2 add_tax:      {step2}")
    print(f"  Step 3 round_values: {step3}")
    print()
    print(f"  Original unchanged:  {raw}")
    print()
    print("  Each step produces a new dict — originals never touched.")


# ══════════════════════════════════════════════════════════════════════════════
# PART 4: Named tuples as immutable records
#
# typing.NamedTuple / collections.namedtuple creates immutable record types.
# Attempting to set a field raises AttributeError.
# Use ._replace(**changes) to create a modified copy.
# ══════════════════════════════════════════════════════════════════════════════

from typing import NamedTuple


class TripRecord(NamedTuple):
    """Immutable trip record. Fields cannot be changed after creation."""
    trip_id: str
    distance: float
    fare: float
    status: str = "raw"


def demo_named_tuple():
    print("\n" + "=" * 55)
    print("PART 4: NamedTuple — immutable records")
    print("=" * 55)
    print()

    trip = TripRecord(trip_id="T01", distance=4.5, fare=12.75)
    print(f"  Original: {trip}")

    # _replace returns a NEW namedtuple with the specified fields changed
    validated = trip._replace(status="validated")
    print(f"  After _replace(status='validated'): {validated}")
    print(f"  Original unchanged: {trip}")

    print()
    print("  Trying to mutate directly (will raise AttributeError):")
    try:
        trip.status = "validated"   # type: ignore
    except AttributeError as e:
        print(f"    AttributeError: {e}")

    print()
    print("  NamedTuple advantages:")
    print("    • Fields accessible by name (trip.fare) AND by index (trip[2])")
    print("    • Equality by value, not identity")
    print(f"    • {trip == TripRecord('T01', 4.5, 12.75)}  ← two tuples with same values are equal")


def main():
    demo_dict_update()
    demo_list_operations()
    demo_immutable_pipeline()
    demo_named_tuple()


if __name__ == "__main__":
    main()

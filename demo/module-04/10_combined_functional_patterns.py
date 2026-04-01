"""
10_combined_functional_patterns.py
=====================================
A complete record-processing pipeline that combines all Module 4 techniques:

  Closures          → configurable validators and transformers
  functools.partial → bind common arguments once, reuse everywhere
  lru_cache         → avoid re-running expensive lookups
  Function composition (pipe) → compose stages into a single callable
  Immutability      → every transform returns a NEW record; originals untouched
  Generators        → process records lazily without buffering the full set

The pipeline processes taxi trip records through:
  1. Sanitise  — strip whitespace, normalise case (pipe composition)
  2. Validate  — check required fields, fare range (closures + partial)
  3. Enrich    — look up zone labels (lru_cache for the lookup)
  4. Emit      — yield results lazily (generator)

Run:
    python demo/module-04/10_combined_functional_patterns.py
"""

import time
from functools import lru_cache, partial, reduce
from typing import Callable, Generator, NamedTuple


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def pipe(*fns: Callable) -> Callable:
    """Apply fns left-to-right: pipe(f, g)(x) == g(f(x))."""
    def piped(value):
        return reduce(lambda v, f: f(v), fns, value)
    return piped


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 1: Sanitise — pipe composition + immutable dict update
#
# sanitise(record) applies a sequence of single-responsibility transforms.
# Each transform uses {**record, key: new_value} — original never changed.
#
# Flow for sanitise({"trip_id": " T01 ", "zone": "NORTH "}):
#   1. _strip_strings    → {"trip_id": "T01", "zone": "NORTH"}
#   2. _lowercase_zone   → {"trip_id": "T01", "zone": "north"}
# ══════════════════════════════════════════════════════════════════════════════

def _strip_strings(record: dict) -> dict:
    """Return new record with all string fields stripped."""
    return {k: v.strip() if isinstance(v, str) else v for k, v in record.items()}


def _lowercase_zone(record: dict) -> dict:
    """Return new record with zone field lowercased (if present)."""
    if "zone" in record and isinstance(record["zone"], str):
        return {**record, "zone": record["zone"].lower()}
    return record


# Compose the two sanitise steps into a single callable
sanitise = pipe(_strip_strings, _lowercase_zone)


def demo_stage1_sanitise():
    print("=" * 60)
    print("STAGE 1: Sanitise (pipe composition + immutable update)")
    print("=" * 60)
    print()

    dirty = {"trip_id": "  T01  ", "fare": 12.5, "zone": " NORTH "}
    clean = sanitise(dirty)
    print(f"  Input:  {dirty}")
    print(f"  Output: {clean}")
    print(f"  Original unchanged: {dirty}")


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 2: Validate — closures + functools.partial
#
# make_fare_validator(min_fare, max_fare) → closure that checks fare range
# make_field_validator(field, predicate)  → closure that checks a field
#
# partial is used to create reusable validators with pre-bound arguments.
#
# Flow for validate(record):
#   1. Each validator is called with record
#   2. If ALL validators pass → {**record, "_valid": True}
#   3. If ANY fails           → {**record, "_valid": False, "_reason": "..."}
# ══════════════════════════════════════════════════════════════════════════════

def make_fare_validator(min_fare: float, max_fare: float) -> Callable:
    """Closure: returns a validator that checks fare is in [min_fare, max_fare].

    Flow: make_fare_validator(5.0, 100.0)
      → validator = closure capturing min_fare=5.0, max_fare=100.0
      → validator(record) returns (True, "") or (False, reason_string)
    """
    def validator(record: dict):
        fare = record.get("fare")
        if not isinstance(fare, (int, float)):
            return False, f"fare is not numeric: {fare!r}"
        if not (min_fare <= fare <= max_fare):
            return False, f"fare {fare} outside [{min_fare}, {max_fare}]"
        return True, ""
    return validator


def make_field_required(field_name: str) -> Callable:
    """Closure: returns a validator that checks field_name is present and non-empty."""
    def validator(record: dict):
        val = record.get(field_name)
        if val is None or val == "":
            return False, f"required field '{field_name}' is missing or empty"
        return True, ""
    return validator


def make_composite_validator(*validators: Callable) -> Callable:
    """Return a validator that runs all validators; returns first failure or (True, '').

    Flow: make_composite_validator(v1, v2, v3)(record)
      → v1(record) → if fail: return (False, reason) immediately (short-circuit)
      → v2(record) → ...
      → all passed → return (True, "")
    """
    def composite(record: dict):
        for v in validators:
            ok, reason = v(record)
            if not ok:
                return False, reason
        return True, ""
    return composite


# Build the project-level validator using partial to bind args once
_fare_ok   = make_fare_validator(min_fare=5.0, max_fare=150.0)
_id_ok     = make_field_required("trip_id")
_zone_ok   = make_field_required("zone")

validate_record = make_composite_validator(_id_ok, _zone_ok, _fare_ok)


def apply_validation(record: dict) -> dict:
    """Run the composite validator; return new record stamped with _valid / _reason.

    Flow: validate_record(record)
      → (True, "")     → {**record, "_valid": True}
      → (False, reason) → {**record, "_valid": False, "_reason": reason}
    """
    ok, reason = validate_record(record)
    if ok:
        return {**record, "_valid": True}
    return {**record, "_valid": False, "_reason": reason}


def demo_stage2_validate():
    print("\n" + "=" * 60)
    print("STAGE 2: Validate (closures + partial + compositeValidator)")
    print("=" * 60)
    print()

    records = [
        {"trip_id": "T01", "zone": "north", "fare": 12.50},
        {"trip_id": "T02", "zone": "north", "fare": 3.00},    # fare too low
        {"trip_id": "",    "zone": "south", "fare": 20.00},   # missing trip_id
        {"trip_id": "T04", "zone": "",      "fare": 8.00},    # missing zone
        {"trip_id": "T05", "zone": "east",  "fare": 200.00},  # fare too high
    ]

    print(f"  {'trip_id':<6}  {'zone':<6}  {'fare':>6}  {'valid':<6}  reason")
    print(f"  {'-'*6}  {'-'*6}  {'-'*6}  {'-'*5}  ------")
    for r in records:
        result = apply_validation(r)
        valid  = result["_valid"]
        reason = result.get("_reason", "")
        print(f"  {r['trip_id']!r:<6}  {r['zone']!r:<6}  {r['fare']:>6.2f}  "
              f"{'OK' if valid else 'FAIL':<6}  {reason}")


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 3: Enrich — lru_cache for expensive lookups
#
# get_zone_label(zone_code) simulates a slow external lookup (DB / API).
# With lru_cache(maxsize=32), each zone is looked up at most once per run.
#
# Flow for enrich(record):
#   1. get_zone_label(record["zone"])  ← may be a cache hit
#   2. return {**record, "zone_label": label}
# ══════════════════════════════════════════════════════════════════════════════

@lru_cache(maxsize=32)
def get_zone_label(zone_code: str) -> str:
    """Simulated slow zone-label lookup (cached after first call for each zone)."""
    print(f"  [LOOKUP] zone_code={zone_code!r} ← executing (not cached)")
    time.sleep(0.05)
    labels = {
        "north": "Northern District",
        "south": "Southern District",
        "east":  "Eastern District",
        "west":  "Western District",
    }
    return labels.get(zone_code, "Unknown Zone")


def enrich(record: dict) -> dict:
    """Return a new record with zone_label added (lru_cache minimises lookups).

    Flow: enrich({"zone": "north", ...})
      → get_zone_label("north")  [cached after first call]
      → {**record, "zone_label": "Northern District"}
    """
    zone_label = get_zone_label(record.get("zone", ""))
    return {**record, "zone_label": zone_label}


def demo_stage3_enrich():
    print("\n" + "=" * 60)
    print("STAGE 3: Enrich (lru_cache for zone label lookups)")
    print("=" * 60)
    print()

    records = [
        {"trip_id": "T01", "zone": "north", "fare": 12.50},
        {"trip_id": "T02", "zone": "south", "fare": 8.00},
        {"trip_id": "T03", "zone": "north", "fare": 15.00},  # cache hit for 'north'
        {"trip_id": "T04", "zone": "east",  "fare": 22.00},
        {"trip_id": "T05", "zone": "north", "fare": 9.50},   # cache hit
    ]

    print("  Enriching records (watch for '[LOOKUP]' prints — should be 3, not 5):")
    enriched = [enrich(r) for r in records]
    print()
    print(f"  Cache info: {get_zone_label.cache_info()}")
    for r in enriched:
        print(f"    {r['trip_id']}: zone={r['zone']!r} → {r['zone_label']!r}")


# ══════════════════════════════════════════════════════════════════════════════
# FULL PIPELINE: all stages as a generator
#
# Stages are chained lazily: records flow through one at a time.
# Only valid records reach the enrich stage.
#
# Flow:
#   for record in raw_records          (generator — lazy source)
#     → sanitise(record)               (immutable transform)
#     → apply_validation(record)       (closure-based validators)
#     → if _valid: enrich(record)      (lru_cache lookup)
#     → yield result                   (lazy output)
# ══════════════════════════════════════════════════════════════════════════════

def process_records(raw_records: list) -> Generator[dict, None, None]:
    """Full pipeline: sanitise → validate → enrich (lazy generator).

    Yields only valid, enriched records.
    Invalid records are silently dropped (extend to collect errors as needed).
    """
    for raw in raw_records:
        record    = sanitise(raw)
        validated = apply_validation(record)
        if validated["_valid"]:
            yield enrich(validated)


def demo_full_pipeline():
    print("\n" + "=" * 60)
    print("FULL PIPELINE: sanitise → validate → enrich (generator)")
    print("=" * 60)
    print()

    raw_data = [
        {"trip_id": "  T01  ", "zone": " NORTH ", "fare": 12.50},
        {"trip_id": "T02",     "zone": "south",   "fare": 3.00},   # fare too low
        {"trip_id": "",        "zone": "east",    "fare": 8.00},   # missing id
        {"trip_id": "T04",     "zone": " WEST ",  "fare": 22.00},
        {"trip_id": "T05",     "zone": "north",   "fare": 9.50},
        {"trip_id": "T06",     "zone": "south",   "fare": 200.00}, # fare too high
        {"trip_id": "T07",     "zone": "east",    "fare": 11.00},
    ]

    print(f"  Input:  {len(raw_data)} raw records")
    print()

    # The pipeline is a generator — nothing processes until we iterate
    pipeline = process_records(raw_data)

    results = list(pipeline)

    print()
    print(f"  Output: {len(results)} valid enriched records")
    print()
    for r in results:
        _valid = r.pop("_valid", None)   # remove internal bookkeeping for display
        print(f"    {r}")

    print()
    print(f"  lru_cache stats: {get_zone_label.cache_info()}")
    print()
    print("  ── Techniques used ─────────────────────────────────────")
    print("  Closures          → make_fare_validator, make_field_required")
    print("  Composition       → pipe(strip_strings, lowercase_zone)")
    print("  partial / closure → composite_validator from smaller validators")
    print("  lru_cache         → get_zone_label (each zone looked up once)")
    print("  Immutability      → every transform returns a new dict")
    print("  Generator         → process_records yields lazily")


def main():
    demo_stage1_sanitise()
    demo_stage2_validate()
    demo_stage3_enrich()
    demo_full_pipeline()


if __name__ == "__main__":
    main()

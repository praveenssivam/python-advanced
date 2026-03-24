"""
src/validify/main.py — CLI entry point for the validation pipeline.

─────────────────────────────────────────────────────────
DAY 1 TASK (create this file)
─────────────────────────────────────────────────────────
Create a runner that produces the same output as starter/validate_trips.py
but uses the new class hierarchy:

  1. Accept a CSV path from sys.argv[1].
  2. Open the CSV with open() + csv.DictReader (plain, no context manager yet).
  3. Instantiate rules manually:
       rules = [NullCheckRule("vendor_id"), RangeRule("passenger_count", 1, 8), ...]
  4. For each record, call each rule: result = rule(record)  # __call__
  5. Collect ValidationResult objects.
  6. Print a summary (same format as the starter script).

─────────────────────────────────────────────────────────
DAY 2 TASK (update this file)
─────────────────────────────────────────────────────────
  - Apply @timeit to the main validation function.
  - Build a Report dataclass from the results and print pass_rate from it.

─────────────────────────────────────────────────────────
DAY 3 TASK (update this file)
─────────────────────────────────────────────────────────
  - Replace the hardcoded rules list with:
      rules = RuleFactory.from_config("config/rules.yaml")
  - Wrap the CSV open() in DatasetLoader context manager (stretch).
  - Run records through normalize_record before validation.

─────────────────────────────────────────────────────────
Run with:
    python src/validify/main.py data/taxi_trips_sample.csv
─────────────────────────────────────────────────────────
"""

"""
src/validify/main.py — CLI entry point for the validation pipeline.

─────────────────────────────────────────────────────────
Day 1 implementation notes
─────────────────────────────────────────────────────────
This file produces the same summary output as starter/validate_trips.py,
but the internal structure is fundamentally different:

  1. Rules are objects, not free functions.
     rule(record) calls __call__ on BaseValidator — the object owns its logic.
  2. The rules list IS the pipeline configuration.
     On Day 3 this hardcoded list is replaced by RuleFactory.from_config().
  3. Results are ValidationResult objects collected into a plain list.
     On Day 2 these are wrapped in a Report dataclass with a pass_rate property.
  4. The CSV is opened with plain open() + csv.DictReader.
     On Day 3 a DatasetLoader context manager replaces this.

Compare this file with starter/validate_trips.py side-by-side:
  - Same behaviour, same summary format.
  - Different structure: standalone functions → class hierarchy.
  - Same dataset, reproducible counts — a good self-check after each day.

Progression:
  Day 1 → hardcoded rule list, plain open(), plain list of results
  Day 2 → @timeit decorator, Report dataclass, pass_rate property
  Day 3 → RuleFactory.from_config(), normalize_record(), DatasetLoader
  Day 4 → runner moves to engine/runner.py, exposed via FastAPI
─────────────────────────────────────────────────────────

Run with:
    python src/validify/main.py data/taxi_trips_sample.csv
"""

import csv
import sys
from pathlib import Path

from validify.rules.built_in import (
    CoordinateRule,
    DateFormatRule,
    NullCheckRule,
    RangeRule,
)


def _build_rules():
    """Return the Day 1 hardcoded rule list.

    Every rule here mirrors a check_* function in starter/validate_trips.py,
    making the function-to-class migration easy to trace.

    Two checks present in the starter are intentionally absent here:
      - payment_type: requires RegexRule, which is added on Day 3.
      - trip_duration: requires a two-field rule — a class design exercise
        for Day 2 stretch.

    Because of these two missing rules the pass rate will be higher than the
    starter's 50.0%. That gap is worth examining: it shows that coverage
    depends on which rules are included, not just how they are structured.

    On Day 3 this entire function is replaced by a single line:
        return RuleFactory.from_config("config/rules.yaml")
    """
    return [
        # ── null checks (mirror check_not_null calls) ───────────────────────
        NullCheckRule("vendor_id"),
        NullCheckRule("pickup_datetime"),
        NullCheckRule("dropoff_datetime"),
        NullCheckRule("total_amount"),
        # ── numeric ranges (mirror check_range calls) ───────────────────────
        RangeRule("passenger_count", min_val=1,    max_val=8),
        RangeRule("trip_distance",   min_val=0.1,  max_val=200.0),
        RangeRule("fare_amount",     min_val=0.01, max_val=500.0),
        RangeRule("total_amount",    min_val=0.01, max_val=600.0),
        # ── coordinate bounds (mirror check_coordinate calls) ────────────────
        CoordinateRule("pickup_lon",  min_val=-75.0, max_val=-72.0),
        CoordinateRule("pickup_lat",  min_val=40.0,  max_val=42.0),
        CoordinateRule("dropoff_lon", min_val=-75.0, max_val=-72.0),
        CoordinateRule("dropoff_lat", min_val=40.0,  max_val=42.0),
        # ── date format (stretch) ─────────────────────────────────────────────
        DateFormatRule("pickup_datetime"),
        DateFormatRule("dropoff_datetime"),
    ]


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python src/validify/main.py <path/to/trips.csv>")
        sys.exit(1)

    csv_path = Path(sys.argv[1])
    if not csv_path.exists():
        print(f"Error: file not found — {csv_path}")
        sys.exit(1)

    rules = _build_rules()

    # ── open CSV without a context manager (Day 3: switch to DatasetLoader) ──
    f = open(csv_path, newline="", encoding="utf-8")
    reader = csv.DictReader(f)

    results = []          # flat list of ValidationResult — Day 2: wrap in Report
    record_count = 0

    for record in reader:
        record_count += 1
        # Results are collected per record so the final summary can report
        # at record granularity ("N records passed"), matching the starter output.
        record_results = [rule(record) for rule in rules]
        results.extend(record_results)

    f.close()

    # ── summary (same format as starter/validate_trips.py) ───────────────────
    # A record "passes" only if every rule check on it passes — the same
    # semantics as check_record() in validate_trips.py.
    n_rules = len(rules)
    records_passed = 0
    records_failed = 0
    failed_record_details: dict[int, list] = {}

    for i in range(record_count):
        chunk = results[i * n_rules : (i + 1) * n_rules]
        failures = [r for r in chunk if not r.passed]
        if failures:
            records_failed += 1
            failed_record_details[i + 1] = failures
        else:
            records_passed += 1

    pass_rate = (records_passed / record_count * 100) if record_count else 0.0

    print(f"\nValidation complete — {csv_path.name}")
    print(f"  Records   : {record_count}")
    print(f"  Passed    : {records_passed}")
    print(f"  Failed    : {records_failed}")
    print(f"  Pass rate : {pass_rate:.1f}%")

    if failed_record_details:
        print(f"\nFirst 5 failing records:")
        for rec_idx, failures in list(failed_record_details.items())[:5]:
            print(f"  Record #{rec_idx}:")
            for r in failures:
                print(f"    [{r.rule}] {r.message}")

    # ── Day 2 TODO ────────────────────────────────────────────────────────────
    # from validify.utils.decorators import timeit
    # from validify.core.models import Report
    # Wrap the validation loop with @timeit; build Report(results) and use
    # report.pass_rate instead of computing it manually above.


if __name__ == "__main__":
    main()


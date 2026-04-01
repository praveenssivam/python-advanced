"""
main.py
========
Demonstrates how to import from a sibling module (helpers.py)
and the effect of the __name__ guard.

Run from the repository root:
    python module-01/03_modules_demo/main.py
"""

import sys
import os

# Make the parent directory available so helpers.py can be found
# when running as: python module-01/03_modules_demo/main.py
sys.path.insert(0, os.path.dirname(__file__))

# ── Import styles ────────────────────────────────────────────────────────────

# Style 1: import the whole module, access with dot notation
import helpers

# Style 2: import specific names directly into this namespace
from helpers import clamp, DailyLog


def demo_module_import():
    print("=" * 50)
    print("SECTION 1: Using helpers via 'import helpers'")
    print("=" * 50)

    result = helpers.format_record("throughput", 1_024.5, "records/s")
    print(result)

    summary = helpers.batch_summary([
        {"name": "run1", "value": 12.4},
        {"name": "run2", "value": 15.1},
        {"name": "run3", "value": 9.8},
    ])
    print(f"Batch summary: {summary}")


def demo_direct_import():
    print("\n" + "=" * 50)
    print("SECTION 2: Using clamp imported directly from helpers")
    print("=" * 50)

    raw_pct = 130.0
    clamped = clamp(raw_pct, 0, 100)
    print(f"clamp({raw_pct}, 0, 100) = {clamped}")
    print("Useful when a sensor overflows its expected range.")


def demo_class_from_module():
    print("\n" + "=" * 50)
    print("SECTION 3: Using DailyLog imported directly from helpers")
    print("=" * 50)

    log = DailyLog(label="temperature_sensor_A")
    log.record(36.5)
    log.record(37.1)
    log.record(36.8)

    print(f"Log object: {log}")
    print(f"Summary: {log.summary()}")


def demo_name_guard():
    print("\n" + "=" * 50)
    print("SECTION 4: The __name__ guard")
    print("=" * 50)
    print(f"This file's __name__ : {__name__!r}")
    print(f"helpers module __name__: {helpers.__name__!r}")
    print()
    print("When you run main.py, main.__name__ is '__main__'.")
    print("When helpers.py is imported, helpers.__name__ is 'helpers', not '__main__'.")
    print("This is why code wrapped in 'if __name__ == \"__main__\"' only runs when the file is the entry point.")


def main():
    demo_module_import()
    demo_direct_import()
    demo_class_from_module()
    demo_name_guard()


if __name__ == "__main__":
    main()

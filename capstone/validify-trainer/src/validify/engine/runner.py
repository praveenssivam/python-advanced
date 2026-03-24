"""
engine/runner.py — Validation execution engines.

─────────────────────────────────────────────────────────
DAY 4 TASK — Part A (mandatory)
─────────────────────────────────────────────────────────
Implement two execution functions and benchmark them.

1. run_sequential(records, rules) -> list[ValidationResult]
   — Plain for-loop over records, calling each rule on each record.
   — This is the baseline. Apply @timeit to measure it.

2. run_threaded(records, rules, workers=4) -> list[ValidationResult]
   — Use ThreadPoolExecutor(max_workers=workers).
   — Each submitted task validates one record against all rules.
   — Protect the shared results list with a threading.Lock().
   — Apply @timeit and compare the elapsed time with run_sequential.

After both are working, add a comment at the top of this file:
    # sequential: X.XXs   threaded(4): X.XXs   (measured on taxi_trips_sample.csv)

─────────────────────────────────────────────────────────
DISCUSSION QUESTION (think about this while you implement)
─────────────────────────────────────────────────────────
Why does threading not always make CPU-bound work faster in Python?
What would change if you used ProcessPoolExecutor instead?

─────────────────────────────────────────────────────────
DAY 4 TASK — Part B (stretch)
─────────────────────────────────────────────────────────
3. async def run_async(records, rules) -> list[ValidationResult]
   — Use asyncio.gather with a list of coroutines.
   — Each coroutine validates one record against all rules.
   — Return the flattened list of ValidationResult objects.
"""

import asyncio  # noqa: F401
from concurrent.futures import ThreadPoolExecutor  # noqa: F401
from threading import Lock  # noqa: F401

from validify.core.base import BaseValidator  # noqa: F401
from validify.core.models import ValidationResult  # noqa: F401

# Apply your @timeit decorator here once you have implemented it in utils/decorators.py


# ---------------------------------------------------------------------------
# YOUR CODE BELOW
# ---------------------------------------------------------------------------

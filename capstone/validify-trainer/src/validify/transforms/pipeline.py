"""
transforms/pipeline.py — Functional transformation pipeline.

─────────────────────────────────────────────────────────
DAY 3 TASK — Part A (mandatory)
─────────────────────────────────────────────────────────
1. Implement pipe(*fns) using functools.reduce:

       pipe(f, g, h)(x)  ==  h(g(f(x)))

   Each function takes one value and returns one value.
   Use functools.reduce to chain them left to right.

   Example:
       strip  = lambda d: {k: v.strip() for k, v in d.items()}
       result = pipe(strip, normalize_record)(raw_record)

2. Implement normalize_record(record: dict) -> dict:
   - Strip leading/trailing whitespace from all string values.
   - That is the minimum. Keep it simple.

─────────────────────────────────────────────────────────
DAY 3 TASK — Part B (stretch)
─────────────────────────────────────────────────────────
3. Implement DatasetLoader as a context manager:

       class DatasetLoader:
           def __init__(self, path: str) -> None: ...
           def __enter__(self) -> Iterator[dict]: ...
           def __exit__(self, *args) -> None: ...

   - Opens the CSV file in __enter__.
   - Yields a generator of dict rows (one per CSV row).
   - Does NOT load the full file into memory (use csv.DictReader lazily).
   - Closes the file handle in __exit__.
   - Raises DataLoadError (from core.exceptions) if the file is not found.

   Usage in main.py (after implementation):
       with DatasetLoader("data/taxi_trips_sample.csv") as records:
           for record in records:
               ...
"""

import csv  # noqa: F401
from functools import reduce  # noqa: F401
from typing import Callable, Iterator, TypeVar  # noqa: F401

from validify.core.exceptions import DataLoadError  # noqa: F401

T = TypeVar("T")


# ---------------------------------------------------------------------------
# YOUR CODE BELOW
# ---------------------------------------------------------------------------

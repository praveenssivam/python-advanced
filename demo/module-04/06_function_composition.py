"""
06_function_composition.py
============================
Function composition: chaining multiple single-purpose functions so that
the output of each function becomes the input to the next.

  compose(f, g, h)(x)  ≡  f(g(h(x)))

This is the functional equivalent of the Builder or Pipeline pattern.

Run:
    python demo/module-04/06_function_composition.py
"""

import re
from functools import reduce
from typing import Callable


# ══════════════════════════════════════════════════════════════════════════════
# PART 1: compose() helper
#
# compose(*fns) builds a single callable from a sequence of functions.
# The rightmost function is applied first; its result is fed into the next.
#
# Flow for compose(add_prefix, uppercase, strip_spaces)("  hello  "):
#   1. strip_spaces("  hello  ") → "hello"
#   2. uppercase("hello")        → "HELLO"
#   3. add_prefix("HELLO")       → "COL: HELLO"
#
# pipe(*fns) is the same but left-to-right (first function applied first).
# Use whichever feels more natural for your team.
# ══════════════════════════════════════════════════════════════════════════════

def compose(*fns: Callable) -> Callable:
    """Return a new function that applies fns right-to-left.

    compose(f, g, h)(x) == f(g(h(x)))
    """
    def composed(value):
        # reduce: start with value, apply each function in reverse order
        return reduce(lambda v, f: f(v), reversed(fns), value)
    return composed


def pipe(*fns: Callable) -> Callable:
    """Return a new function that applies fns left-to-right.

    pipe(f, g, h)(x) == h(g(f(x)))
    Easier to read as 'first do f, then g, then h'.
    """
    def piped(value):
        return reduce(lambda v, f: f(v), fns, value)
    return piped


def demo_compose_helpers():
    print("=" * 55)
    print("PART 1: compose() and pipe() helpers")
    print("=" * 55)
    print()

    def add_one(n): return n + 1
    def double(n):  return n * 2
    def square(n):  return n ** 2

    # compose: right-to-left → square first, then double, then add_one
    transform_compose = compose(add_one, double, square)
    # pipe:    left-to-right → add_one first, then double, then square
    transform_pipe = pipe(add_one, double, square)

    n = 3
    print(f"  Input: {n}")
    print()
    print(f"  compose(add_one, double, square)({n}):  "
          f"square({n})={n**2} → double={n**2*2} → add_one={n**2*2+1}  "
          f"→ {transform_compose(n)}")
    print(f"  pipe(add_one, double, square)({n}):     "
          f"add_one({n})={n+1} → double={( n+1)*2} → square={(( n+1)*2)**2}  "
          f"→ {transform_pipe(n)}")


# ══════════════════════════════════════════════════════════════════════════════
# PART 2: Practical pipeline — normalising messy column names
#
# Raw column names from CSV headers often have:
#   • leading/trailing whitespace
#   • mixed case
#   • special characters (punctuation, slashes)
#   • multiple consecutive spaces
#   • spaces that should become underscores
#
# Each step is a single-responsibility function.
# Compose them once; apply to any iterable of column names.
#
# Flow for normalize_column(" Trip Duration (min) "):
#   1. strip_whitespace     → "Trip Duration (min)"
#   2. to_lowercase         → "trip duration (min)"
#   3. remove_special_chars → "trip duration min"
#   4. normalize_spaces     → "trip duration min"
#   5. replace_spaces       → "trip_duration_min"
# ══════════════════════════════════════════════════════════════════════════════

def strip_whitespace(s: str) -> str:
    """Remove leading and trailing whitespace."""
    return s.strip()


def to_lowercase(s: str) -> str:
    """Convert to lowercase."""
    return s.lower()


def remove_special_chars(s: str) -> str:
    """Remove characters that are not alphanumeric or whitespace."""
    return re.sub(r"[^a-z0-9\s]", "", s)


def normalize_spaces(s: str) -> str:
    """Collapse multiple consecutive spaces into one."""
    return re.sub(r"\s+", " ", s).strip()


def replace_spaces(s: str) -> str:
    """Replace spaces with underscores."""
    return s.replace(" ", "_")


# Compose into a single normalizer — steps applied left-to-right
normalize_column = pipe(
    strip_whitespace,
    to_lowercase,
    remove_special_chars,
    normalize_spaces,
    replace_spaces,
)


def demo_column_normalizer():
    print("\n" + "=" * 55)
    print("PART 2: Column name normalisation pipeline")
    print("=" * 55)
    print()

    messy_columns = [
        "  Trip Duration (min)  ",
        "Pickup/Dropoff Location",
        "FARE AMOUNT $",
        "  tip%  ",
        "Passenger   Count",
        "payment_type",               # already clean — should be unchanged
    ]

    print(f"  {'Raw column':<32s}  {'Normalised'}")
    print(f"  {'-'*32}  {'-'*25}")
    for raw in messy_columns:
        cleaned = normalize_column(raw)
        print(f"  {repr(raw):<32s}  {cleaned}")

    print()
    print("  compose steps: strip → lower → remove_special → "
          "collapse_spaces → underscores")


# ══════════════════════════════════════════════════════════════════════════════
# PART 3: Building different pipelines from the same building blocks
#
# Because each step is a plain function, you can mix and match to build
# different pipelines for different use cases without any class hierarchy.
# ══════════════════════════════════════════════════════════════════════════════

def demo_different_pipelines():
    print("\n" + "=" * 55)
    print("PART 3: Different pipelines from the same building blocks")
    print("=" * 55)
    print()

    # Pipeline A: just clean whitespace and lowercase (for display labels)
    display_label = pipe(strip_whitespace, to_lowercase)

    # Pipeline B: full normalisation without underscores (for human-readable names)
    human_readable = pipe(
        strip_whitespace,
        to_lowercase,
        remove_special_chars,
        normalize_spaces,
    )

    # Pipeline C: the full snake_case normalizer defined above
    raw = "  Payment Type (%)  "

    print(f"  Input: {repr(raw)}")
    print(f"  Pipeline A (label only):     {display_label(raw)!r}")
    print(f"  Pipeline B (human readable): {human_readable(raw)!r}")
    print(f"  Pipeline C (snake_case):     {normalize_column(raw)!r}")

    print()
    print("  Same building blocks; different assembly, different outcome.")


# ══════════════════════════════════════════════════════════════════════════════
# PART 4: Composing validation predicates
#
# Predicates (bool-returning functions) can be composed using and/or logic.
# all_of(preds)(value) → True only if every predicate returns True.
# any_of(preds)(value) → True if at least one predicate returns True.
# ══════════════════════════════════════════════════════════════════════════════

def all_of(*preds: Callable) -> Callable:
    """Return a combined predicate: True iff all preds(value) are True."""
    def combined(value):
        return all(p(value) for p in preds)
    return combined


def any_of(*preds: Callable) -> Callable:
    """Return a combined predicate: True iff any pred(value) is True."""
    def combined(value):
        return any(p(value) for p in preds)
    return combined


def demo_predicate_composition():
    print("\n" + "=" * 55)
    print("PART 4: Composing validation predicates")
    print("=" * 55)
    print()

    is_not_empty  = lambda s: len(s) > 0
    is_short      = lambda s: len(s) <= 20
    starts_alpha  = lambda s: s[:1].isalpha() if s else False
    no_whitespace = lambda s: " " not in s

    valid_identifier = all_of(is_not_empty, is_short, starts_alpha, no_whitespace)

    test_values = ["trip_id", "", "this_name_is_way_too_long_to_be_valid",
                   "123starts_with_digit", "has space"]

    print(f"  {'Value':<40s}  valid_identifier")
    print(f"  {'-'*40}  ----------------")
    for v in test_values:
        print(f"  {repr(v):<40s}  {valid_identifier(v)}")


def main():
    demo_compose_helpers()
    demo_column_normalizer()
    demo_different_pipelines()
    demo_predicate_composition()


if __name__ == "__main__":
    main()

"""
03_functools_partial.py
=========================
functools.partial pre-fills one or more arguments of a callable,
returning a new callable that accepts only the remaining arguments.

Problem:  Repeated calls with the same base arguments — verbose and error-prone.
Solution: partial() creates a specialised version of a function for a specific
          context with selected arguments pre-filled.

Run:
    python demo/module-04/03_functools_partial.py
"""

from functools import partial


# ══════════════════════════════════════════════════════════════════════════════
# PART 1: What partial does
#
# partial(func, *args, **kwargs) → new callable
#
# The returned callable, when called, merges:
#   - the pre-filled args/kwargs supplied to partial()
#   - the positional/keyword args supplied in the actual call
# … and passes the combined result to the original function.
#
# Flow for partial(multiply, factor=3):
#   1. Stores func=multiply, kwargs={"factor": 3}
#   2. Returns a new callable   p
#   3. p(10)
#      → multiply(10, factor=3)
#      → 10 * 3 → 30
# ══════════════════════════════════════════════════════════════════════════════

def multiply(x: float, factor: float) -> float:
    """Multiply x by factor."""
    return x * factor


def pad_string(value: str, width: int, fill_char: str = " ") -> str:
    """Right-pad value to width using fill_char."""
    return value.ljust(width, fill_char)


def demo_partial_basics():
    print("=" * 55)
    print("PART 1: partial() — pre-fill arguments")
    print("=" * 55)
    print()

    # Without partial — repeated keyword every call
    print("Without partial:")
    for x in [5, 10, 15]:
        print(f"  multiply({x}, factor=3) = {multiply(x, factor=3)}")

    print()
    # Flow: partial(multiply, factor=3)
    #   → stores factor=3
    #   → triple(10) → multiply(10, factor=3) → 30
    triple = partial(multiply, factor=3)
    print("With partial(multiply, factor=3):")
    for x in [5, 10, 15]:
        print(f"  triple({x}) = {triple(x)}")

    print()
    # partial with both positional and keyword pre-fills
    pad_to_20 = partial(pad_string, width=20, fill_char="-")
    print("partial(pad_string, width=20, fill_char='-'):")
    for word in ["sensor_id", "region", "amount"]:
        print(f"  pad_to_20({word!r}) = {pad_to_20(word)!r}")


# ══════════════════════════════════════════════════════════════════════════════
# PART 2: Practical uses in data pipelines
#
# 1. Type conversion: partial(int, base=16) → int-from-hex converter
# 2. Validation: partial(validate_column, schema=SCHEMA) → column validator
# 3. Logging: partial(log, level="INFO") → info-level logger
# 4. Mapping: pass partial to map() or apply_to_each() for concise transforms
# ══════════════════════════════════════════════════════════════════════════════

def validate_column(value: str, field_name: str, min_len: int, max_len: int) -> bool:
    """Return True if value passes length bounds for field_name."""
    result = min_len <= len(value) <= max_len
    print(f"  validate {field_name!r}: {value!r} → {'✓' if result else '✗'}")
    return result


def format_row(row: dict, template: str, sep: str = " | ") -> str:
    """Format a row dict using a template list of keys."""
    return sep.join(str(row[k]) for k in template.split(","))


def demo_pipeline_partials():
    print("\n" + "=" * 55)
    print("PART 2: Practical partial applications")
    print("=" * 55)
    print()

    # ── convert hex strings to int ───────────────────────────────────────────
    # Flow: partial(int, base=16) → hex_to_int
    #   hex_to_int("FF") → int("FF", base=16) → 255
    hex_to_int = partial(int, base=16)
    hex_codes = ["1A", "FF", "3C", "00"]
    print("hex_to_int via partial(int, base=16):")
    for h in hex_codes:
        print(f"  hex_to_int({h!r}) = {hex_to_int(h)}")

    print()
    # ── field validator pinning length bounds ────────────────────────────────
    # Flow: partial(validate_column, field_name="username", min_len=3, max_len=20)
    #   validate_username("alice") → validate_column("alice", "username", 3, 20)
    validate_username = partial(
        validate_column, field_name="username", min_len=3, max_len=20
    )
    print("Column validator via partial:")
    for val in ["alice", "ab", "this_name_is_way_too_long_for_a_username"]:
        validate_username(val)

    print()
    # ── row formatter for reports ─────────────────────────────────────────────
    # Flow: partial(format_row, template="city,count", sep=" | ")
    #   city_row({"city": "Mumbai", "count": 1200}) → "Mumbai | 1200"
    city_formatter = partial(format_row, template="city,count", sep=" | ")
    rows = [{"city": "Mumbai", "count": 1200}, {"city": "Delhi", "count": 980}]
    print("Row formatter via partial:")
    for row in rows:
        print(f"  {city_formatter(row)}")


# ══════════════════════════════════════════════════════════════════════════════
# PART 3: partial vs. lambda vs. closure — comparison
#
# All three can "freeze" arguments into a new callable. The choice
# depends on clarity and the number of pre-filled arguments.
#
#   partial  → clearest when pre-filling existing functions
#   lambda   → concise for one-offs; loses original function name
#   closure  → best when the factory logic is complex or configurable
# ══════════════════════════════════════════════════════════════════════════════

def scale(value: float, minimum: float, maximum: float) -> float:
    """Normalise value to [0, 1] using min-max scaling."""
    if maximum == minimum:
        return 0.0
    return (value - minimum) / (maximum - minimum)


def demo_comparison():
    print("\n" + "=" * 55)
    print("PART 3: partial vs. lambda vs. closure")
    print("=" * 55)
    print()

    values = [10.0, 25.0, 50.0, 75.0, 100.0]
    lo, hi = 10.0, 100.0

    # partial
    scale_0_100 = partial(scale, minimum=lo, maximum=hi)

    # lambda (equivalent, but anonymous)
    scale_lambda = lambda v: scale(v, lo, hi)  # noqa: E731

    # closure
    def make_scaler(lo, hi):
        def _scale(v): return scale(v, lo, hi)
        return _scale
    scale_closure = make_scaler(lo, hi)

    print(f"Scale values from [{lo}, {hi}] to [0, 1]:")
    print(f"  {'value':>6}  {'partial':>8}  {'lambda':>8}  {'closure':>8}")
    for v in values:
        print(f"  {v:>6.1f}  "
              f"{scale_0_100(v):>8.3f}  "
              f"{scale_lambda(v):>8.3f}  "
              f"{scale_closure(v):>8.3f}")

    print()
    print("All three produce the same result.")
    print("partial is most readable when pre-filling a known function.")
    print(f"partial func name preserved: {scale_0_100.func.__name__!r}")
    print(f"partial keywords stored:     {scale_0_100.keywords}")


def main():
    demo_partial_basics()
    demo_pipeline_partials()
    demo_comparison()


if __name__ == "__main__":
    main()

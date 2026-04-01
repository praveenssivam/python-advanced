"""
02_closures.py
================
A closure is a function that captures variables from its enclosing scope.
The captured variables survive as long as the inner function is alive —
even after the outer function has returned.

Run:
    python demo/module-04/02_closures.py
"""


# ══════════════════════════════════════════════════════════════════════════════
# PART 1: What a closure is
#
# When Python defines an inner function inside an outer function:
#   1. The inner function has a reference to the outer function's local scope.
#   2. When the outer function returns, its locals are NOT destroyed —
#      they are kept alive in a 'cell' object as long as the inner function exists.
#   3. The inner function can READ those captured variables freely.
#
# The inner function + the captured cells together = a closure.
#
# Inspect closure cells via: inner_fn.__closure__[n].cell_contents
# ══════════════════════════════════════════════════════════════════════════════

def make_multiplier(factor: float):
    """Return a function that multiplies its argument by factor.

    factor is captured in the closure — survives after make_multiplier returns.

    Flow for make_multiplier(3):
      1. Python enters make_multiplier, factor=3
      2. Defines multiply(x) — captures 'factor' from enclosing scope
      3. Returns multiply (the closure object)
      4. make_multiplier is done; its frame is gone, but factor lives in a cell
    """
    def multiply(x: float) -> float:
        return x * factor       # 'factor' read from closure cell
    return multiply


def demo_basic_closure():
    print("=" * 55)
    print("PART 1: Basic closure — capturing a single variable")
    print("=" * 55)
    print()

    # Flow: make_multiplier(3) → returns multiply with factor=3 in closure
    triple = make_multiplier(3)
    double = make_multiplier(2)

    print(f"triple(10)  = {triple(10)}")    # 30
    print(f"double(10)  = {double(10)}")    # 20
    print(f"triple(2.5) = {triple(2.5)}")   # 7.5

    # Confirm each closure captures its OWN factor cell
    print()
    print(f"triple.__closure__[0].cell_contents = {triple.__closure__[0].cell_contents}")
    print(f"double.__closure__[0].cell_contents = {double.__closure__[0].cell_contents}")
    print("triple and double are independent — they capture separate values.")


# ══════════════════════════════════════════════════════════════════════════════
# PART 2: Closures as configurable function factories
#
# The classic use-case: make_validator(criteria) → validator function.
# Each validator remembers its own criteria without needing a class.
#
# Flow for make_length_validator(min_len=3, max_len=20):
#   → captures min_len=3, max_len=20
#   → returns validate(value)
#   Later calls to validate("alice"):
#     → reads min_len=3, max_len=20 from closure
#     → returns True/False
# ══════════════════════════════════════════════════════════════════════════════

def make_length_validator(min_len: int, max_len: int):
    """Factory: return a validator that checks string length."""

    def validate(value: str) -> tuple[bool, str]:
        n = len(value)
        if n < min_len:
            return False, f"too short: got {n}, min is {min_len}"
        if n > max_len:
            return False, f"too long: got {n}, max is {max_len}"
        return True, ""

    return validate


def make_prefix_validator(prefix: str):
    """Factory: return a validator that checks for a specific prefix."""

    def validate(value: str) -> tuple[bool, str]:
        if value.startswith(prefix):
            return True, ""
        return False, f"must start with {prefix!r}, got {value!r}"

    return validate


def make_range_validator(lo: float, hi: float):
    """Factory: return a validator that checks numeric ranges."""

    def validate(value: str) -> tuple[bool, str]:
        try:
            n = float(value)
        except ValueError:
            return False, f"{value!r} is not a number"
        if not (lo <= n <= hi):
            return False, f"{n} is outside [{lo}, {hi}]"
        return True, ""

    return validate


def run_validators(validators: list, value: str) -> None:
    """Run all validators against value; print each result."""
    all_pass = True
    for fn in validators:
        ok, reason = fn(value)
        status = "✓" if ok else "✗"
        print(f"  {status} {value!r}  → {reason if not ok else 'ok'}")
        if not ok:
            all_pass = False
    if all_pass:
        print(f"  All validators passed for {value!r}")


def demo_validator_closures():
    print("\n" + "=" * 55)
    print("PART 2: Configurable validators via closures")
    print("=" * 55)
    print()

    username_validators = [
        make_length_validator(min_len=3, max_len=20),
        make_prefix_validator(prefix="usr_"),
    ]

    for val in ["usr_alice", "al", "usr_" + "a" * 20, "nodontstart"]:
        run_validators(username_validators, val)
        print()

    print("Score range validator (0.0 – 1.0):")
    score_val = make_range_validator(0.0, 1.0)
    for s in ["0.85", "1.2", "not_a_float"]:
        ok, reason = score_val(s)
        print(f"  {'✓' if ok else '✗'} {s!r}  → {reason if not ok else 'ok'}")


# ══════════════════════════════════════════════════════════════════════════════
# PART 3: Closures with mutable state — accumulators
#
# An inner function can MODIFY an enclosed variable using the `nonlocal`
# keyword. This creates a stateful callable — like a lightweight object.
#
# Flow for make_counter():
#   → count = 0  (cell variable)
#   → returns increment()
#   Each call to increment():
#     → nonlocal count   (refers to the cell in the enclosing scope)
#     → count += 1       (modifies the cell)
#     → return count
# ══════════════════════════════════════════════════════════════════════════════

def make_counter(start: int = 0, step: int = 1):
    """Return (increment, reset) pair that share a closure over 'count'."""

    count = start

    def increment() -> int:
        nonlocal count          # signal: this 'count' lives in the closure, not locally
        count += step
        return count

    def reset() -> None:
        nonlocal count
        count = start

    return increment, reset


def make_running_average():
    """Return a function that maintains a running average over all calls."""

    total = 0.0
    n = 0

    def update(value: float) -> float:
        nonlocal total, n
        total += value
        n += 1
        return total / n        # current average over all seen values

    return update


def demo_stateful_closures():
    print("\n" + "=" * 55)
    print("PART 3: Stateful closures with nonlocal")
    print("=" * 55)
    print()

    # Flow: make_counter(start=0, step=2)
    #   → count=0 in closure
    #   → increment() adds step=2 each call
    increment, reset = make_counter(start=0, step=2)
    print("Counter (step=2):")
    for _ in range(4):
        print(f"  increment() = {increment()}")
    reset()
    print(f"  After reset: {increment()}")

    print()
    # Flow: make_running_average() → captures total=0.0, n=0
    #   Each average(x) call → total += x, n += 1 → total/n
    average = make_running_average()
    readings = [10.0, 20.0, 30.0, 40.0]
    print("Running average over sensor readings:")
    for r in readings:
        print(f"  average({r}) = {average(r):.2f}")


def main():
    demo_basic_closure()
    demo_validator_closures()
    demo_stateful_closures()


if __name__ == "__main__":
    main()

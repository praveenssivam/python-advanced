"""
06_strategy_pattern.py
========================
Strategy Pattern — define a family of algorithms, encapsulate each one,
and make them interchangeable at runtime.

The object that uses the strategy (the context) selects behaviour without
knowing the implementation details of each strategy.

Run:
    python demo/module-03/06_strategy_pattern.py
"""

import re
from abc import ABC, abstractmethod


# ══════════════════════════════════════════════════════════════════════════════
# CONTEXT: FieldValidator
#
# Without the strategy pattern, FieldValidator would contain all validation
# logic directly — if/elif for each algorithm variant.
#
# With the strategy pattern:
#   - FieldValidator is the CONTEXT — it knows it must validate, but not how.
#   - Each ValidationStrategy is a concrete algorithm.
#   - The caller selects the right strategy; the context just runs it.
#
# Runtime flow for FieldValidator.validate(value):
#   1. self._strategy.check(value) is called
#   2. Execution enters the concrete strategy's check() implementation
#   3. Result (True/False + reason) is returned to the caller
#   The context never branches on strategy type — it treats them uniformly.
# ══════════════════════════════════════════════════════════════════════════════

class ValidationStrategy(ABC):
    """Abstract strategy — one check algorithm."""

    @abstractmethod
    def check(self, value: str) -> tuple[bool, str]:
        """Return (is_valid, reason). reason is empty string when valid."""
        ...

    @property
    @abstractmethod
    def name(self) -> str: ...


# ── Concrete strategies ──────────────────────────────────────────────────────

class LengthStrategy(ValidationStrategy):
    """Strategy: value must be between min_len and max_len characters."""

    name = "length"

    def __init__(self, min_len: int = 1, max_len: int = 255):
        self._min = min_len
        self._max = max_len

    def check(self, value: str) -> tuple[bool, str]:
        n = len(value)
        if n < self._min:
            return False, f"too short ({n} < {self._min})"
        if n > self._max:
            return False, f"too long ({n} > {self._max})"
        return True, ""


class RegexStrategy(ValidationStrategy):
    """Strategy: value must fully match a regular expression."""

    name = "regex"

    def __init__(self, pattern: str):
        self._re = re.compile(pattern)
        self._pattern_str = pattern

    def check(self, value: str) -> tuple[bool, str]:
        if self._re.fullmatch(value):
            return True, ""
        return False, f"does not match {self._pattern_str!r}"


class AllowlistStrategy(ValidationStrategy):
    """Strategy: value must be one of a pre-approved set."""

    name = "allowlist"

    def __init__(self, allowed: set[str]):
        self._allowed = allowed

    def check(self, value: str) -> tuple[bool, str]:
        if value in self._allowed:
            return True, ""
        return False, f"{value!r} not in allowlist {sorted(self._allowed)}"


class NumericRangeStrategy(ValidationStrategy):
    """NEW strategy — added without modifying FieldValidator or any other strategy."""

    name = "numeric_range"

    def __init__(self, lo: float, hi: float):
        self._lo = lo
        self._hi = hi

    def check(self, value: str) -> tuple[bool, str]:
        try:
            n = float(value)
        except ValueError:
            return False, f"{value!r} is not a number"
        if not (self._lo <= n <= self._hi):
            return False, f"{n} outside range [{self._lo}, {self._hi}]"
        return True, ""


# ── Context ──────────────────────────────────────────────────────────────────

class FieldValidator:
    """Context: validates a value using an injected strategy.

    The strategy can be swapped at any time without changing this class.
    """

    def __init__(self, field_name: str, strategy: ValidationStrategy):
        self._field = field_name
        self._strategy = strategy

    @property
    def strategy(self) -> ValidationStrategy:
        return self._strategy

    @strategy.setter
    def strategy(self, new_strategy: ValidationStrategy) -> None:
        self._strategy = new_strategy

    def validate(self, value: str) -> bool:
        """Run the current strategy against value; print result."""
        # Flow: FieldValidator.validate(value)
        #   → self._strategy.check(value)   (runtime dispatch)
        #   → returns (is_valid, reason)
        ok, reason = self._strategy.check(value)
        status = "✓" if ok else "✗"
        desc = f"  [{status}] {self._field!r} = {value!r}"
        if not ok:
            desc += f"  ← {reason}"
        print(desc)
        return ok


def demo_strategy():
    print("=" * 60)
    print("Strategy Pattern — validation algorithm selected at runtime")
    print("=" * 60)
    print()

    # ── Length strategy ──────────────────────────────────────────────────────
    print("FieldValidator with LengthStrategy(min=3, max=20):")
    v = FieldValidator("username", LengthStrategy(min_len=3, max_len=20))
    for val in ["alice", "ab", "a" * 25]:
        v.validate(val)

    # ── Swap strategy at runtime — no new FieldValidator needed ──────────────
    print()
    print("Swapping to RegexStrategy (lowercase alphanumeric only):")
    v.strategy = RegexStrategy(r"[a-z][a-z0-9_]*")
    for val in ["alice", "Alice", "123start", "col_name"]:
        v.validate(val)

    # ── AllowlistStrategy ────────────────────────────────────────────────────
    print()
    print("FieldValidator with AllowlistStrategy for 'status' field:")
    status_v = FieldValidator(
        "status",
        AllowlistStrategy({"pending", "running", "complete", "failed"})
    )
    for val in ["running", "complete", "unknown", "RUNNING"]:
        status_v.validate(val)

    # ── New strategy added — FieldValidator unchanged ────────────────────────
    print()
    print("New NumericRangeStrategy — FieldValidator code unchanged:")
    score_v = FieldValidator("score", NumericRangeStrategy(lo=0.0, hi=1.0))
    for val in ["0.85", "1.2", "-0.1", "not_a_number"]:
        score_v.validate(val)

    print()
    print("All strategies are interchangeable. Adding a new one requires")
    print("only a new subclass — FieldValidator is never modified.")


def demo_if_elif_comparison():
    print("\n" + "=" * 60)
    print("Comparison: if/elif approach (alternative, for contrast)")
    print("=" * 60)
    print()

    def validate_with_ifelif(value: str, rule_type: str, **kwargs) -> bool:
        """Illustrates the problem: adding 'allowlist' means adding another elif."""
        if rule_type == "length":
            return kwargs["min_len"] <= len(value) <= kwargs["max_len"]
        elif rule_type == "regex":
            return bool(re.fullmatch(kwargs["pattern"], value))
        # ← adding "numeric_range" here means editing this function forever
        return True

    # Works, but closed to extension
    print(f"  length check 'alice': {validate_with_ifelif('alice', 'length', min_len=3, max_len=20)}")
    print()
    print("  To add 'numeric_range': edit validate_with_ifelif.")
    print("  Strategy pattern: add NumericRangeStrategy class — nothing else.")


def main():
    demo_strategy()
    demo_if_elif_comparison()


if __name__ == "__main__":
    main()

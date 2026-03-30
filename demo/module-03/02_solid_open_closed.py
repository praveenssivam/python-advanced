"""
02_solid_open_closed.py
========================
Open/Closed Principle (OCP) — the O in SOLID.

Problem:  A validator uses if/elif to handle each rule type.
          Adding a new rule requires modifying the existing function.
Solution: Define an abstract rule interface; each rule is a class.
          Adding a new rule is adding a new class — existing code untouched.

Run:
    python demo/module-03/02_solid_open_closed.py
"""

import re
from abc import ABC, abstractmethod


# ══════════════════════════════════════════════════════════════════════════════
# PART 1: VIOLATION — closed to extension, open to modification
#
# Every time a new validation rule type is needed, the engineer must
# open validate_field() and add another elif branch.
#
# Why this hurts:
#   - Each change risks breaking existing branches.
#   - Adding a new rule type requires a code review of the entire function.
#   - The function grows without bound.
#   - Can't load rules from config (they're hardcoded as special-cases).
# ══════════════════════════════════════════════════════════════════════════════

def validate_field_bad(value: str, rules: list[dict]) -> list[str]:
    """BAD: adds a new elif for every new rule type.

    Rules are dicts: {"type": "min_length", "value": 5} etc.
    To add "starts_with" rule: open this function, add another elif.
    Risk: every modification can break existing rule types.
    """
    errors = []
    for rule in rules:
        kind = rule["type"]
        if kind == "min_length":
            if len(value) < rule["value"]:
                errors.append(f"Too short (min {rule['value']})")
        elif kind == "max_length":
            if len(value) > rule["value"]:
                errors.append(f"Too long (max {rule['value']})")
        elif kind == "regex":
            if not re.fullmatch(rule["pattern"], value):
                errors.append(f"Does not match pattern {rule['pattern']!r}")
        # ← Adding "starts_with" means editing HERE every time
    return errors


def demo_violation():
    print("=" * 60)
    print("PART 1: OCP Violation — if/elif grows with every new rule type")
    print("=" * 60)
    print()

    rules = [
        {"type": "min_length", "value": 3},
        {"type": "max_length", "value": 20},
        {"type": "regex", "pattern": r"[a-z0-9_]+"},
    ]

    # Flow: validate_field_bad("ab", rules)
    #   → kind="min_length" → len("ab")=2 < 3 → error added
    #   → kind="max_length" → ok
    #   → kind="regex"      → ok
    for test in ["ok_value", "ab", "UPPER_CASE", "a" * 25]:
        errs = validate_field_bad(test, rules)
        status = "✓" if not errs else "✗"
        print(f"  {status} {test!r:20s}  {errs}")

    print()
    print("To add a 'starts_with' rule: must edit validate_field_bad().")
    print("Every edit risks breaking all other rule types.")


# ══════════════════════════════════════════════════════════════════════════════
# PART 2: REFACTORED — open for extension, closed for modification
#
# ValidationRule is an abstract class. Each rule type is a concrete subclass.
# The FieldValidator simply calls rule.validate(value) on each rule.
#
# To add a new rule type: write a new subclass — FieldValidator never changes.
#
# Flow for FieldValidator.validate(value):
#   For each rule in self._rules:
#     rule.validate(value) → returns list of error strings (empty = no error)
#   Collect all errors → return combined list
# ══════════════════════════════════════════════════════════════════════════════

class ValidationRule(ABC):
    """Abstract contract: every rule can validate a single string value."""

    @abstractmethod
    def validate(self, value: str) -> list[str]:
        """Return a list of error messages; empty list means the value is valid."""
        ...


class MinLengthRule(ValidationRule):
    """Requires the value to be at least min_length characters long."""

    def __init__(self, min_length: int):
        self._min = min_length

    def validate(self, value: str) -> list[str]:
        if len(value) < self._min:
            return [f"Too short: got {len(value)}, minimum is {self._min}"]
        return []


class MaxLengthRule(ValidationRule):
    """Requires the value to be at most max_length characters long."""

    def __init__(self, max_length: int):
        self._max = max_length

    def validate(self, value: str) -> list[str]:
        if len(value) > self._max:
            return [f"Too long: got {len(value)}, maximum is {self._max}"]
        return []


class RegexRule(ValidationRule):
    """Requires the value to fully match a regular expression."""

    def __init__(self, pattern: str):
        self._pattern = re.compile(pattern)
        self._raw = pattern

    def validate(self, value: str) -> list[str]:
        if not self._pattern.fullmatch(value):
            return [f"Does not match pattern {self._raw!r}"]
        return []


# ── New rule added WITHOUT modifying any of the above ────────────────────────

class StartsWithRule(ValidationRule):
    """NEW RULE: requires the value to begin with a specific prefix.

    Adding this rule required zero changes to MinLengthRule, MaxLengthRule,
    RegexRule, or FieldValidator. OCP is satisfied.
    """

    def __init__(self, prefix: str):
        self._prefix = prefix

    def validate(self, value: str) -> list[str]:
        if not value.startswith(self._prefix):
            return [f"Must start with {self._prefix!r}"]
        return []


class FieldValidator:
    """Runs a list of ValidationRule instances against a single value.

    FieldValidator is open for extension (accept new rules) and
    closed for modification (its logic never changes when rules are added).
    """

    def __init__(self, rules: list[ValidationRule]):
        self._rules = rules

    def validate(self, value: str) -> list[str]:
        """Collect and return all rule errors for value."""
        # Flow: for each rule → call rule.validate(value) → accumulate errors
        errors = []
        for rule in self._rules:
            errors.extend(rule.validate(value))
        return errors


def demo_ocp():
    print("\n" + "=" * 60)
    print("PART 2: OCP Applied — new rule types via new classes only")
    print("=" * 60)
    print()

    validator = FieldValidator(rules=[
        MinLengthRule(min_length=3),
        MaxLengthRule(max_length=20),
        RegexRule(pattern=r"[a-z0-9_]+"),
    ])

    print("Validator with 3 rules (MinLength, MaxLength, Regex):")
    for test in ["ok_value", "ab", "UPPER_CASE", "a" * 25]:
        errs = validator.validate(test)
        status = "✓" if not errs else "✗"
        print(f"  {status} {test!r:20s}  {errs}")

    print()
    print("Adding StartsWithRule — FieldValidator code unchanged:")
    validator_with_prefix = FieldValidator(rules=[
        MinLengthRule(min_length=3),
        MaxLengthRule(max_length=20),
        RegexRule(pattern=r"[a-z0-9_]+"),
        StartsWithRule(prefix="col_"),       # NEW — no existing code modified
    ])

    for test in ["col_sensor_a", "ok_value", "col_"]:
        errs = validator_with_prefix.validate(test)
        status = "✓" if not errs else "✗"
        print(f"  {status} {test!r:20s}  {errs}")

    print()
    print("StartsWithRule was written and dropped in — no existing code changed.")


def main():
    demo_violation()
    demo_ocp()


if __name__ == "__main__":
    main()

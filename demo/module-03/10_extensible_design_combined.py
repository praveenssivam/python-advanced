"""
10_extensible_design_combined.py
===================================
Combines Strategy, Factory, and Observer patterns in a single cohesive
validation engine.

  ValidationEngine uses the Strategy pattern to run rules.
  ConnectorFactory builds rule objects from config (Factory pattern).
  ValidationListener observers receive events on every check (Observer).

Adding a new rule type: write a rule class + factory.register() call.
Adding a new observer:  write a listener class + engine.attach() call.
The ValidationEngine never changes.

Run:
    python demo/module-03/10_extensible_design_combined.py
"""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


# ══════════════════════════════════════════════════════════════════════════════
# 1. STRATEGY — ValidationRule
# ══════════════════════════════════════════════════════════════════════════════

class ValidationRule(ABC):
    """Strategy interface: one self-contained check algorithm."""

    @abstractmethod
    def check(self, field_name: str, value: str) -> list[str]:
        """Return list of error messages; empty = valid."""
        ...

    @property
    @abstractmethod
    def rule_type(self) -> str: ...


class MinLengthRule(ValidationRule):
    rule_type = "min_length"

    def __init__(self, min_length: int, **kwargs):
        self._min = min_length

    def check(self, field_name: str, value: str) -> list[str]:
        if len(value) < self._min:
            return [f"{field_name}: too short (min {self._min}, got {len(value)})"]
        return []


class MaxLengthRule(ValidationRule):
    rule_type = "max_length"

    def __init__(self, max_length: int, **kwargs):
        self._max = max_length

    def check(self, field_name: str, value: str) -> list[str]:
        if len(value) > self._max:
            return [f"{field_name}: too long (max {self._max}, got {len(value)})"]
        return []


class RegexRule(ValidationRule):
    rule_type = "regex"

    def __init__(self, pattern: str, **kwargs):
        self._re = re.compile(pattern)
        self._pattern = pattern

    def check(self, field_name: str, value: str) -> list[str]:
        if not self._re.fullmatch(value):
            return [f"{field_name}: does not match {self._pattern!r}"]
        return []


class AllowlistRule(ValidationRule):
    """NEW strategy — added via factory, zero engine changes."""

    rule_type = "allowlist"

    def __init__(self, values: list[str], **kwargs):
        self._allowed = set(values)

    def check(self, field_name: str, value: str) -> list[str]:
        if value not in self._allowed:
            return [f"{field_name}: {value!r} not in {sorted(self._allowed)}"]
        return []


# ══════════════════════════════════════════════════════════════════════════════
# 2. FACTORY — RuleFactory
# ══════════════════════════════════════════════════════════════════════════════

class RuleFactory:
    """Registry-based factory for ValidationRule instances.

    Flow for RuleFactory.create(config):
      1. Extract "type" key from config dict.
      2. Look up in _registry.
      3. Return rule_class(**remaining_config).
    """

    _registry: dict[str, type[ValidationRule]] = {}

    @classmethod
    def register(cls, type_name: str, rule_class: type[ValidationRule]) -> None:
        cls._registry[type_name] = rule_class

    @classmethod
    def create(cls, config: dict) -> ValidationRule:
        cfg = dict(config)
        type_name = cfg.pop("type")
        if type_name not in cls._registry:
            raise ValueError(f"Unknown rule type {type_name!r}. Known: {sorted(cls._registry)}")
        return cls._registry[type_name](**cfg)


RuleFactory.register("min_length", MinLengthRule)
RuleFactory.register("max_length", MaxLengthRule)
RuleFactory.register("regex",      RegexRule)
RuleFactory.register("allowlist",  AllowlistRule)


# ══════════════════════════════════════════════════════════════════════════════
# 3. OBSERVER — ValidationListener
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class ValidationEvent:
    field_name: str
    value: str
    errors: list[str]

    @property
    def is_valid(self) -> bool:
        return not self.errors


class ValidationListener(ABC):
    """Observer interface for validation events."""

    @abstractmethod
    def on_checked(self, event: ValidationEvent) -> None: ...


class AuditListener(ValidationListener):
    """Prints a structured audit log for every field check."""

    def on_checked(self, event: ValidationEvent) -> None:
        status = "PASS" if event.is_valid else "FAIL"
        print(f"  [AUDIT] {status} {event.field_name!r} = {event.value!r}", end="")
        if event.errors:
            print(f"  → {event.errors[0]}")
        else:
            print()


class SummaryListener(ValidationListener):
    """Accumulates pass/fail counts; prints a summary on demand."""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.failures: list[str] = []

    def on_checked(self, event: ValidationEvent) -> None:
        if event.is_valid:
            self.passed += 1
        else:
            self.failed += 1
            self.failures.extend(event.errors)

    def report(self) -> None:
        total = self.passed + self.failed
        print(f"  [SUMMARY] {self.passed}/{total} passed, {self.failed} failed")
        for f in self.failures:
            print(f"    ✗ {f}")


class StrictListener(ValidationListener):
    """NEW observer — raises immediately on first failure (strict mode)."""

    def on_checked(self, event: ValidationEvent) -> None:
        if not event.is_valid:
            raise ValueError(f"Strict validation failed: {event.errors[0]}")


# ══════════════════════════════════════════════════════════════════════════════
# 4. ENGINE — ties Strategy + Factory + Observer together
# ══════════════════════════════════════════════════════════════════════════════

class ValidationEngine:
    """Runs a set of rules against a data record and notifies listeners.

    Engine never references concrete rule classes or listener classes.
    Everything is injected — strategies via RuleFactory, listeners via attach().

    Flow for engine.validate(record):
      For each (field_name, value) in record:
        For each rule in self._rules:
          errors = rule.check(field_name, value)   ← Strategy dispatch
          emit ValidationEvent to all listeners    ← Observer notify
    """

    def __init__(self, rule_configs: list[dict]):
        # Build rule objects from config dicts via the Factory
        self._rules: list[ValidationRule] = [
            RuleFactory.create(cfg) for cfg in rule_configs
        ]
        self._listeners: list[ValidationListener] = []

    def attach(self, listener: ValidationListener) -> None:
        self._listeners.append(listener)

    def _notify(self, event: ValidationEvent) -> None:
        for listener in self._listeners:
            listener.on_checked(event)

    def validate(self, record: dict[str, str]) -> bool:
        """Validate all fields in the record. Returns True if fully valid."""
        all_valid = True
        for field_name, value in record.items():
            errors: list[str] = []
            for rule in self._rules:
                errors.extend(rule.check(field_name, value))

            event = ValidationEvent(field_name=field_name, value=value, errors=errors)
            self._notify(event)  # ← Observer notify

            if errors:
                all_valid = False
        return all_valid


# ══════════════════════════════════════════════════════════════════════════════
# DEMO
# ══════════════════════════════════════════════════════════════════════════════

def demo_combined():
    print("=" * 60)
    print("Combined: Strategy + Factory + Observer in a validation engine")
    print("=" * 60)
    print()

    # Rules are pure config — no constructor calls in business code
    rule_configs = [
        {"type": "min_length", "min_length": 3},
        {"type": "max_length", "max_length": 30},
        {"type": "regex",      "pattern": r"[a-z][a-z0-9_]*"},
    ]

    summary = SummaryListener()

    # Flow: ValidationEngine.__init__(configs)
    #   → RuleFactory.create(cfg) for each config → MinLengthRule, MaxLengthRule, RegexRule
    engine = ValidationEngine(rule_configs)
    engine.attach(AuditListener())
    engine.attach(summary)

    records = [
        {"username": "alice", "col_name": "trip_distance"},
        {"username": "ab", "col_name": "UPPER_CASE"},
        {"username": "valid_user_name_here", "col_name": "x"},
    ]

    for rec in records:
        print(f"  Record: {rec}")
        engine.validate(rec)
        print()

    summary.report()


def demo_new_rule_and_listener():
    print("\n" + "=" * 60)
    print("Adding AllowlistRule + StrictListener — engine unchanged")
    print("=" * 60)
    print()

    # AllowlistRule was registered earlier; just use it in config
    rule_configs = [
        {"type": "allowlist", "values": ["pending", "running", "complete", "failed"]},
    ]

    engine = ValidationEngine(rule_configs)
    engine.attach(AuditListener())
    engine.attach(StrictListener())  # NEW observer — engine code unchanged

    print("  Validating 'status' values with StrictListener active:")
    for val in ["running", "complete", "unknown"]:
        try:
            # Flow: engine.validate() → AllowlistRule.check() → notify observers
            #   → StrictListener raises on first failure
            engine.validate({"status": val})
        except ValueError as e:
            print(f"  [STRICT] Stopped: {e}")
            break


def main():
    demo_combined()
    demo_new_rule_and_listener()


if __name__ == "__main__":
    main()

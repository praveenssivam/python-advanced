"""
10_validation_service_concurrent.py
=====================================
Real-world pattern: concurrent rule evaluation in a data validation engine.

Problem:
  - Each validation rule takes time (DB lookup, regex, format check).
  - Running rules sequentially adds latency for every record.
  - Rules are INDEPENDENT — no rule depends on another's result.
  - ThreadPoolExecutor lets all rules evaluate simultaneously.

Demo scenario:
  Record → [EmailRule(0.10s)] ──┐
           [LengthRule(0.01s)] ─┼─ concurrent → combined result
           [RegexRule(0.02s)]  ──┘

  Sequential total: 0.10 + 0.01 + 0.02 = 0.13s per record
  Concurrent total: max(0.10, 0.01, 0.02) = 0.10s per record

Run:
    python demo/module-05/10_validation_service_concurrent.py
"""

import time
import re
import threading
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Protocol


# ══════════════════════════════════════════════════════════════════════════════
# Domain model
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Record:
    id: int
    email: str
    name: str
    age: int


@dataclass
class RuleResult:
    rule_name: str
    passed: bool
    message: str = ""
    elapsed: float = 0.0


@dataclass
class ValidationResult:
    record_id: int
    passed: bool
    rule_results: list[RuleResult] = field(default_factory=list)
    total_elapsed: float = 0.0


# ══════════════════════════════════════════════════════════════════════════════
# Validation rules — each simulates I/O or computation latency
# ══════════════════════════════════════════════════════════════════════════════

class ValidationRule(Protocol):
    """Any callable with validate(record) -> RuleResult."""
    def validate(self, record: Record) -> RuleResult: ...


class EmailRule:
    """
    Simulates a DB lookup to check email uniqueness.
    Latency: 0.10s — represents the slowest rule (network call).
    """
    def validate(self, record: Record) -> RuleResult:
        t0 = time.perf_counter()
        time.sleep(0.10)      # simulate DB round-trip
        passed = "@" in record.email and "." in record.email.split("@")[-1]
        elapsed = time.perf_counter() - t0
        return RuleResult(
            rule_name="EmailRule",
            passed=passed,
            message="" if passed else f"invalid email: {record.email}",
            elapsed=elapsed,
        )


class LengthRule:
    """
    CPU validation — name length check.
    Latency: 0.01s — fast local computation.
    """
    def validate(self, record: Record) -> RuleResult:
        t0 = time.perf_counter()
        time.sleep(0.01)      # simulate complex regex compilation
        passed = 2 <= len(record.name) <= 100
        elapsed = time.perf_counter() - t0
        return RuleResult(
            rule_name="LengthRule",
            passed=passed,
            message="" if passed else f"name length {len(record.name)} out of [2,100]",
            elapsed=elapsed,
        )


class RegexRule:
    """
    Pattern validation — name format check.
    Latency: 0.02s — compiled regex with some overhead.
    """
    _pattern = re.compile(r"^[A-Za-z ,.'-]{2,100}$")

    def validate(self, record: Record) -> RuleResult:
        t0 = time.perf_counter()
        time.sleep(0.02)      # simulate loading pattern from config store
        passed = bool(self._pattern.match(record.name))
        elapsed = time.perf_counter() - t0
        return RuleResult(
            rule_name="RegexRule",
            passed=passed,
            message="" if passed else f"name contains invalid characters: {record.name}",
            elapsed=elapsed,
        )


# ══════════════════════════════════════════════════════════════════════════════
# PART 1: Sequential validation engine
#
# Rules run one-after-another. Total time = sum of all rule latencies.
# ══════════════════════════════════════════════════════════════════════════════

class SequentialValidationEngine:
    def __init__(self, rules: list):
        self._rules = rules

    def validate(self, record: Record) -> ValidationResult:
        t0 = time.perf_counter()
        rule_results = [rule.validate(record) for rule in self._rules]
        overall_passed = all(r.passed for r in rule_results)
        return ValidationResult(
            record_id=record.id,
            passed=overall_passed,
            rule_results=rule_results,
            total_elapsed=time.perf_counter() - t0,
        )


# ══════════════════════════════════════════════════════════════════════════════
# PART 2: Concurrent validation engine
#
# All rules submitted simultaneously to a ThreadPoolExecutor.
# Total time = max(rule latencies) + small overhead.
#
# Safe because:
#   - Each rule only reads the record (no shared mutation).
#   - rule_results list is assembled after all futures complete.
# ══════════════════════════════════════════════════════════════════════════════

class ConcurrentValidationEngine:
    def __init__(self, rules: list, max_workers: int = 8):
        self._rules = rules
        self._max_workers = max_workers

    def validate(self, record: Record) -> ValidationResult:
        t0 = time.perf_counter()
        rule_results = []

        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            futures = {
                executor.submit(rule.validate, record): rule
                for rule in self._rules
            }
            for fut in as_completed(futures):
                rule_results.append(fut.result())

        overall_passed = all(r.passed for r in rule_results)
        return ValidationResult(
            record_id=record.id,
            passed=overall_passed,
            rule_results=sorted(rule_results, key=lambda r: r.rule_name),
            total_elapsed=time.perf_counter() - t0,
        )


# ══════════════════════════════════════════════════════════════════════════════
# Demo harness
# ══════════════════════════════════════════════════════════════════════════════

RECORDS = [
    Record(id=1, email="alice@example.com", name="Alice Smith",  age=30),
    Record(id=2, email="bob-invalid",       name="Bob",          age=25),   # bad email
    Record(id=3, email="carol@corp.io",     name="Carol 123!",   age=40),   # bad name chars
    Record(id=4, email="dan@test.org",      name="Dan",          age=28),
    Record(id=5, email="eve@domain.net",    name="Eve Johnson",  age=35),
]

RULES = [EmailRule(), LengthRule(), RegexRule()]


def demo_sequential():
    print("=" * 60)
    print("SEQUENTIAL validation engine")
    print("=" * 60)
    print()
    engine = SequentialValidationEngine(RULES)

    t0 = time.perf_counter()
    results = [engine.validate(r) for r in RECORDS]
    total = time.perf_counter() - t0

    for res in results:
        status = "PASS" if res.passed else "FAIL"
        failures = [r.message for r in res.rule_results if not r.passed]
        per_rule = ", ".join(f"{r.rule_name}={r.elapsed:.3f}s" for r in res.rule_results)
        print(f"  record {res.record_id}: {status}  [{per_rule}]  total={res.total_elapsed:.3f}s")
        if failures:
            for msg in failures:
                print(f"    → {msg}")

    print(f"\n  Total wall time ({len(RECORDS)} records): {total:.3f}s")
    return total


def demo_concurrent():
    print("\n" + "=" * 60)
    print("CONCURRENT validation engine  (ThreadPoolExecutor)")
    print("=" * 60)
    print()
    engine = ConcurrentValidationEngine(RULES)

    t0 = time.perf_counter()
    results = [engine.validate(r) for r in RECORDS]
    total = time.perf_counter() - t0

    for res in results:
        status = "PASS" if res.passed else "FAIL"
        failures = [r.message for r in res.rule_results if not r.passed]
        per_rule = ", ".join(f"{r.rule_name}={r.elapsed:.3f}s" for r in res.rule_results)
        print(f"  record {res.record_id}: {status}  [{per_rule}]  total={res.total_elapsed:.3f}s")
        if failures:
            for msg in failures:
                print(f"    → {msg}")

    print(f"\n  Total wall time ({len(RECORDS)} records): {total:.3f}s")
    return total


def main():
    t_seq = demo_sequential()
    t_con = demo_concurrent()

    print("\n" + "=" * 60)
    print("COMPARISON")
    print("=" * 60)
    print()
    print(f"  Sequential:   {t_seq:.3f}s")
    print(f"  Concurrent:   {t_con:.3f}s")
    print(f"  Speedup:      {t_seq / t_con:.1f}×")
    print()
    print("  Per-record breakdown:")
    print("    Sequential: 0.10 + 0.01 + 0.02 = 0.13s per record")
    print("    Concurrent: max(0.10, 0.01, 0.02) = 0.10s per record (bottleneck only)")
    print()
    print("  Design notes:")
    print("    - Rules only READ the record — no shared mutation → no lock needed")
    print("    - ConcurrentValidationEngine API is identical to sequential version")
    print("    - Easy to add rules: just append to the rules list")
    print("    - Thread pool reused across records in production (executor as field)")


if __name__ == "__main__":
    main()

"""
10_async_validation_service.py
================================
Real-world async pattern: concurrent rule evaluation in an async API.

Scenario:
  An API endpoint validates each incoming record against 3 rules.
  Each rule involves I/O (DB lookup, cache read, external API).
  Rules are INDEPENDENT — no rule waits for another.

Performance story:
  Sequential (await each rule): 0.10 + 0.05 + 0.08 = 0.23s per record
  Concurrent (gather all rules): max(0.10, 0.05, 0.08) = 0.10s per record
  10 concurrent client requests: still ~0.10s (bounded by slowest rule)

Run:
    python demo/day-06/10_async_validation_service.py
"""

import asyncio
import re
import time
from dataclasses import dataclass, field
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
# Async validation rules
# Each rule is a coroutine — it can await I/O without blocking.
# ══════════════════════════════════════════════════════════════════════════════

class AsyncEmailRule:
    """
    Simulates async DNS/DB lookup for email uniqueness (0.10s).
    Production: await db.fetch("SELECT 1 FROM users WHERE email=$1", email)
    """
    async def validate(self, record: Record) -> RuleResult:
        t0 = time.perf_counter()
        await asyncio.sleep(0.10)
        passed = "@" in record.email and "." in record.email.split("@")[-1]
        return RuleResult(
            rule_name="AsyncEmailRule",
            passed=passed,
            message="" if passed else f"invalid email: {record.email}",
            elapsed=time.perf_counter() - t0,
        )


class AsyncLengthRule:
    """
    Simulates async config fetch to get max/min length constraints (0.05s).
    Production: limits = await cache.get("validation_config")
    """
    async def validate(self, record: Record) -> RuleResult:
        t0 = time.perf_counter()
        await asyncio.sleep(0.05)   # simulate cache lookup for config
        passed = 2 <= len(record.name) <= 100
        return RuleResult(
            rule_name="AsyncLengthRule",
            passed=passed,
            message="" if passed else f"name length {len(record.name)} out of [2,100]",
            elapsed=time.perf_counter() - t0,
        )


class AsyncRegexRule:
    """
    Simulates async rule registry lookup for regex patterns (0.08s).
    Production: pattern = await rules_db.fetch_one("SELECT pattern FROM rules WHERE id=$1")
    """
    _pattern = re.compile(r"^[A-Za-z ,.'-]{2,100}$")

    async def validate(self, record: Record) -> RuleResult:
        t0 = time.perf_counter()
        await asyncio.sleep(0.08)   # simulate pattern registry fetch
        passed = bool(self._pattern.match(record.name))
        return RuleResult(
            rule_name="AsyncRegexRule",
            passed=passed,
            message="" if passed else f"name has invalid chars: {record.name}",
            elapsed=time.perf_counter() - t0,
        )


# ══════════════════════════════════════════════════════════════════════════════
# PART 1: Sequential async validation engine
#
# Each 'await rule.validate(record)' suspends and waits before starting next.
# Total = sum of rule latencies.
# ══════════════════════════════════════════════════════════════════════════════

class SequentialAsyncEngine:
    def __init__(self, rules: list):
        self._rules = rules

    async def validate(self, record: Record) -> ValidationResult:
        t0 = time.perf_counter()
        rule_results = []
        for rule in self._rules:
            r = await rule.validate(record)   # sequential — waits each time
            rule_results.append(r)
        return ValidationResult(
            record_id=record.id,
            passed=all(r.passed for r in rule_results),
            rule_results=rule_results,
            total_elapsed=time.perf_counter() - t0,
        )


# ══════════════════════════════════════════════════════════════════════════════
# PART 2: Concurrent async validation engine
#
# All rules submitted simultaneously via gather().
# Total = max(rule latencies) — bottleneck is the slowest rule.
# ══════════════════════════════════════════════════════════════════════════════

class ConcurrentAsyncEngine:
    def __init__(self, rules: list):
        self._rules = rules

    async def validate(self, record: Record) -> ValidationResult:
        t0 = time.perf_counter()
        rule_results = await asyncio.gather(
            *[rule.validate(record) for rule in self._rules],
            return_exceptions=True,
        )
        # Handle any unexpected exceptions from rules
        final_results = []
        for i, r in enumerate(rule_results):
            if isinstance(r, Exception):
                final_results.append(RuleResult(
                    rule_name=f"rule_{i}",
                    passed=False,
                    message=f"rule error: {r}",
                ))
            else:
                final_results.append(r)

        return ValidationResult(
            record_id=record.id,
            passed=all(r.passed for r in final_results),
            rule_results=sorted(final_results, key=lambda r: r.rule_name),
            total_elapsed=time.perf_counter() - t0,
        )


# ══════════════════════════════════════════════════════════════════════════════
# PART 3: Concurrent endpoint — multiple clients at the same time
#
# With asyncio, a single process can handle many concurrent requests.
# 10 clients each sending a record → all processed concurrently.
# Total ~= time for ONE record, not 10 × record time.
# ══════════════════════════════════════════════════════════════════════════════

RULES = [AsyncEmailRule(), AsyncLengthRule(), AsyncRegexRule()]

RECORDS = [
    Record(id=1, email="alice@example.com",  name="Alice Smith",  age=30),
    Record(id=2, email="bob-invalid",        name="Bob",          age=25),
    Record(id=3, email="carol@corp.io",      name="Carol 123!",   age=40),
    Record(id=4, email="dan@test.org",       name="Dan",          age=28),
    Record(id=5, email="eve@domain.net",     name="Eve Johnson",  age=35),
    Record(id=6, email="frank@example.com",  name="Frank",        age=22),
    Record(id=7, email="grace@corp.net",     name="Grace Lee",    age=45),
    Record(id=8, email="henry@web.io",       name="Henry-Brown",  age=33),
    Record(id=9, email="iris@invalid",       name="Iris",         age=29),
    Record(id=10, email="jack@example.org",  name="Jack Smith",   age=50),
]


async def demo_sequential():
    print("=" * 60)
    print("PART 1: Sequential async validation (await each rule)")
    print("=" * 60)
    print()
    engine = SequentialAsyncEngine(RULES)

    t0 = time.perf_counter()
    results = []
    for record in RECORDS[:5]:       # first 5 records only to keep output manageable
        r = await engine.validate(record)
        results.append(r)
    total = time.perf_counter() - t0

    for res in results:
        status = "PASS" if res.passed else "FAIL"
        per_rule = " | ".join(f"{r.rule_name.replace('Async','').replace('Rule','').lower()}={r.elapsed:.3f}s"
                              for r in res.rule_results)
        print(f"  record {res.record_id}: {status}  [{per_rule}]  total={res.total_elapsed:.3f}s")

    print(f"\n  Wall time (5 records, 1 at a time): {total:.3f}s")
    return total


async def demo_concurrent_records():
    print("\n" + "=" * 60)
    print("PART 2: Concurrent async validation (gather all rules)")
    print("=" * 60)
    print()
    engine = ConcurrentAsyncEngine(RULES)

    # Each record's rules run concurrently; records themselves are sequential
    t0 = time.perf_counter()
    results = []
    for record in RECORDS[:5]:
        r = await engine.validate(record)
        results.append(r)
    total = time.perf_counter() - t0

    for res in results:
        status = "PASS" if res.passed else "FAIL"
        per_rule = " | ".join(f"{r.rule_name.replace('Async','').replace('Rule','').lower()}={r.elapsed:.3f}s"
                              for r in res.rule_results)
        print(f"  record {res.record_id}: {status}  [{per_rule}]  total={res.total_elapsed:.3f}s")

    print(f"\n  Wall time (5 records, 1 at a time, rules concurrent): {total:.3f}s")
    return total


async def demo_concurrent_clients():
    print("\n" + "=" * 60)
    print("PART 3: 10 concurrent clients — all records processed simultaneously")
    print("=" * 60)
    print()
    engine = ConcurrentAsyncEngine(RULES)

    # All 10 records validated at the same time (simulating 10 API clients)
    t0 = time.perf_counter()
    results = await asyncio.gather(*[engine.validate(r) for r in RECORDS])
    total = time.perf_counter() - t0

    passes = sum(1 for r in results if r.passed)
    fails  = sum(1 for r in results if not r.passed)
    print(f"  10 records processed concurrently")
    print(f"  Passed: {passes}   Failed: {fails}")
    print(f"\n  Wall time (10 simultaneous clients): {total:.3f}s")
    print(f"  Single-threaded processes 10 API requests in the time needed for 1!")
    return total


async def main():
    t_seq_rules   = await demo_sequential()
    t_conc_rules  = await demo_concurrent_records()
    t_conc_clients = await demo_concurrent_clients()

    print("\n" + "=" * 60)
    print("PERFORMANCE SUMMARY")
    print("=" * 60)
    print()
    print(f"  Sequential rules, 1 record:      {t_seq_rules/5:.3f}s per record")
    print(f"  Concurrent rules, 1 record:      {t_conc_rules/5:.3f}s per record")
    print(f"  Rule speedup:                    {(t_seq_rules/5)/(t_conc_rules/5):.1f}×")
    print()
    print(f"  Concurrent rules × 10 clients:   {t_conc_clients:.3f}s total")
    print(f"  vs sequential × 10 sequential:   >{t_seq_rules*2:.2f}s would be expected")
    print()
    print("  Design insight:")
    print("  Concurrent rules: speedup = N_rules (when rules are independent)")
    print("  Concurrent clients: speedup = N_clients (pure async fan-out)")
    print("  Combined: async APIs handle thousands of clients on a single thread")


if __name__ == "__main__":
    asyncio.run(main())

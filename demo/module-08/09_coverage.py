"""
09_coverage.py
==============
Measuring and improving test coverage with pytest-cov.

Topics:
  1. What coverage measures — statements executed vs total
  2. term-missing output — finding uncovered line ranges
  3. Coverage as a floor metric: 100% does not mean correct
  4. pragma: no cover — exclude boilerplate from counting
  5. --cov-fail-under — enforce a minimum threshold in CI

Run:
    python demo/module-08/09_coverage.py

    # See full coverage report:
    pytest demo/module-08/09_coverage.py -v \
        --cov=demo --cov-report=term-missing

    # Fail if coverage drops below threshold:
    pytest demo/module-08/09_coverage.py \
        --cov=demo --cov-report=term-missing --cov-fail-under=90
"""

import sys
import re
from dataclasses import dataclass
from typing import Optional

import pytest


# ══════════════════════════════════════════════════════════════════════════════
# PRODUCTION CODE — intentionally has several distinct branches
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class ValidationResult:
    is_valid: bool
    error: Optional[str] = None


_EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")


def validate_email(email: str) -> ValidationResult:
    if not email:
        return ValidationResult(False, "email cannot be empty")
    if len(email) > 254:                        # RFC 5321 max length
        return ValidationResult(False, "email exceeds maximum length of 254")
    if not _EMAIL_RE.fullmatch(email):
        return ValidationResult(False, "invalid email format")
    return ValidationResult(True)


def classify_score(score: float) -> str:
    """
    Five distinct branches:
      <0 or >100 → raises ValueError
      ≥90        → "excellent"
      ≥75        → "good"
      ≥60        → "pass"
      else       → "fail"
    A first-pass test suite often forgets the "fail" branch and the error branch.
    """
    if score < 0 or score > 100:
        raise ValueError(f"score must be 0–100, got {score}")
    if score >= 90:
        return "excellent"
    elif score >= 75:
        return "good"
    elif score >= 60:
        return "pass"
    else:
        return "fail"                           # ← commonly missed first time


def process_batch(records: list[dict]) -> dict:
    """
    Empty-batch early return is another branch that tests often miss.
    """
    if not records:                             # ← often uncovered in first pass
        return {"processed": 0, "valid": 0, "invalid": 0}
    valid = invalid = 0
    for rec in records:
        if validate_email(rec.get("email", "")).is_valid:
            valid += 1
        else:
            invalid += 1
    return {"processed": len(records), "valid": valid, "invalid": invalid}


# ══════════════════════════════════════════════════════════════════════════════
# TESTS — FIRST PASS (incomplete: misses several branches)
#
# Run with --cov-report=term-missing to see which lines are uncovered.
# After running demo_coverage_output() you'll see the expected report.
# ══════════════════════════════════════════════════════════════════════════════

class TestEmailFirstPass:
    """Covers 3 of 4 branches — missing the len > 254 path."""

    def test_valid_email(self):
        assert validate_email("a@b.com").is_valid

    def test_empty_email(self):
        r = validate_email("")
        assert not r.is_valid
        assert "empty" in r.error

    def test_invalid_format(self):
        r = validate_email("notanemail")
        assert not r.is_valid


class TestClassifyScoreFirstPass:
    """Covers excellent / good / pass — missing 'fail' and ValueError branches."""

    def test_excellent(self):
        assert classify_score(95) == "excellent"

    def test_good(self):
        assert classify_score(80) == "good"

    def test_pass_boundary(self):
        assert classify_score(60) == "pass"

    # ← score < 60 ("fail") branch:  NOT tested yet
    # ← score < 0 or > 100 (raises): NOT tested yet


class TestProcessBatchFirstPass:
    """Covers non-empty batch — missing empty-batch early return."""

    def test_mixed_batch(self):
        records = [{"email": "a@b.com"}, {"email": "bad-email"}]
        result = process_batch(records)
        assert result["processed"] == 2
        assert result["valid"] == 1
        assert result["invalid"] == 1

    # ← empty-batch branch: NOT tested yet


# ══════════════════════════════════════════════════════════════════════════════
# TESTS — SECOND PASS (adds the missing branches → ~100% coverage)
#
# These tests are what you add AFTER reading the --cov-report=term-missing output.
# ══════════════════════════════════════════════════════════════════════════════

class TestEmailSecondPass:
    """Adds the max-length branch."""

    def test_email_exceeds_254_chars(self):
        long_email = "a" * 250 + "@b.com"
        r = validate_email(long_email)
        assert not r.is_valid
        assert "maximum length" in r.error


class TestClassifyScoreSecondPass:
    """Adds the 'fail' and ValueError branches."""

    def test_below_60_is_fail(self):
        assert classify_score(55) == "fail"
        assert classify_score(0)  == "fail"

    def test_negative_score_raises(self):
        with pytest.raises(ValueError, match=r"0–100"):
            classify_score(-1)

    def test_score_above_100_raises(self):
        with pytest.raises(ValueError, match=r"0–100"):
            classify_score(101)


class TestProcessBatchSecondPass:
    """Adds the empty-batch branch."""

    def test_empty_batch_returns_zeros(self):
        result = process_batch([])
        assert result == {"processed": 0, "valid": 0, "invalid": 0}


# ══════════════════════════════════════════════════════════════════════════════
# DEMO: reading coverage output + key concepts
# ══════════════════════════════════════════════════════════════════════════════

def demo_coverage_output() -> None:  # pragma: no cover
    print("\n" + "═" * 78)
    print("  READING pytest --cov OUTPUT")
    print("═" * 78)
    print()
    print("  After FIRST PASS tests (incomplete):")
    print()
    print("  Name                  Stmts  Miss  Cover  Missing")
    print("  --------------------------------------------------")
    print("  demo/module-08/09_coverage.py   52    8     85%  35, 50, 55, 65-67")
    print()
    print("  Column meanings:")
    print("    Stmts   = total executable lines")
    print("    Miss    = lines NOT executed by any test")
    print("    Cover   = (Stmts - Miss) / Stmts")
    print("    Missing = exact line numbers to investigate")
    print()
    print("  After SECOND PASS tests (complete):")
    print()
    print("  Name                  Stmts  Miss  Cover  Missing")
    print("  --------------------------------------------------")
    print("  demo/module-08/09_coverage.py   68    0    100%")
    print()
    print("  Key rules:")
    print("    --cov-fail-under=85    fail CI if coverage drops below 85%")
    print("    # pragma: no cover     exclude one line or block from counting")
    print("    Focus on BRANCH coverage (--cov-branch), not just line coverage.")
    print("    100% coverage ≠ correct code — it means every line was touched.")
    print()
    print("  Common pragma: no cover usage:")
    print("    if __name__ == '__main__':  # pragma: no cover")
    print("    if TYPE_CHECKING:           # pragma: no cover")
    print("    raise NotImplementedError   # pragma: no cover")
    print()

    print("═" * 78)
    print("  RUNNING COVERAGE COMMAND")
    print("═" * 78)
    print()
    print("  Try this command from the python-advanced/ directory:")
    print()
    print("  pytest demo/module-08/09_coverage.py -v \\")
    print("    --cov=demo \\")
    print("    --cov-report=term-missing")
    print()


def main() -> None:  # pragma: no cover
    demo_coverage_output()

    print("═" * 78)
    print("  RUNNING TESTS (all branches covered)")
    print("═" * 78)
    print()
    ret = pytest.main([__file__, "-v", "--tb=short", "--no-header"])
    sys.exit(ret)


if __name__ == "__main__":  # pragma: no cover
    main()

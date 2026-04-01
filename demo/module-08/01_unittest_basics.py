"""
01_unittest_basics.py
=====================
The built-in testing framework: unittest.TestCase.

Topics:
  1. TestCase structure and lifecycle (setUp / tearDown)
  2. Assertion methods: assertEqual, assertTrue, assertIn, assertRaises
  3. subTest — loop over cases inside a single test method
  4. Reading test output — F / E / . and the summary line

Run:
    python demo/module-08/01_unittest_basics.py
    python -m unittest demo/module-08/01_unittest_basics.py -v
"""

import unittest
import re
from dataclasses import dataclass
from typing import Optional


# ══════════════════════════════════════════════════════════════════════════════
# PRODUCTION CODE — the module under test
#
# In a real project these functions live in their own file (e.g. validators.py).
# We define them here so the demo is fully self-contained.
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class ValidationResult:
    is_valid: bool
    error: Optional[str] = None


_EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")


def validate_email(email: str) -> ValidationResult:
    if not email:
        return ValidationResult(False, "email cannot be empty")
    if "@" not in email:
        return ValidationResult(False, "missing @")
    if not _EMAIL_RE.fullmatch(email):
        return ValidationResult(False, "invalid email format")
    return ValidationResult(True)


def validate_record(record: dict) -> ValidationResult:
    if not isinstance(record.get("id"), int) or record["id"] <= 0:
        return ValidationResult(False, "id must be a positive integer")
    if not record.get("name") or not str(record["name"]).strip():
        return ValidationResult(False, "name cannot be empty")
    if "email" in record:
        result = validate_email(record["email"])
        if not result.is_valid:
            return result
    return ValidationResult(True)


# ══════════════════════════════════════════════════════════════════════════════
# TEST CLASS 1 — email validator
#
# TestCase lifecycle per method:
#   setUp()  → test_*()  → tearDown()
#
# All three run even if setUp raises (tearDown still runs if setUp succeeds).
# ══════════════════════════════════════════════════════════════════════════════

class TestEmailValidator(unittest.TestCase):

    # ── setup / teardown ──────────────────────────────────────────────────────

    def setUp(self):
        """Runs BEFORE every test method in this class."""
        # Create shared objects once; each test gets a fresh copy.
        self.valid_emails = [
            "alice@example.com",
            "user.name+tag@example.co.uk",
            "user123@sub.domain.org",
        ]
        self.invalid_emails = [
            "",
            "notanemail",
            "missing-domain@",
            "@nodomain.com",
        ]

    def tearDown(self):
        """Runs AFTER every test method, even if the test fails."""
        # Close files, DB connections, etc. here.
        pass  # nothing to release in this demo

    # ── test methods ──────────────────────────────────────────────────────────

    def test_valid_email_passes(self):
        """All addresses in self.valid_emails must be accepted."""
        for email in self.valid_emails:
            with self.subTest(email=email):       # ← loop without hiding which one failed
                result = validate_email(email)
                self.assertTrue(result.is_valid, f"{email!r} should be valid")

    def test_empty_email_fails(self):
        result = validate_email("")
        self.assertFalse(result.is_valid)
        self.assertIsNotNone(result.error)
        self.assertIn("empty", result.error)

    def test_missing_at_sign_fails(self):
        result = validate_email("userexample.com")
        self.assertFalse(result.is_valid)
        self.assertIn("@", result.error)      # error message must mention @

    def test_all_invalid_emails_fail(self):
        for email in self.invalid_emails:
            with self.subTest(email=email):
                result = validate_email(email)
                self.assertFalse(result.is_valid, f"{email!r} should be invalid")


# ══════════════════════════════════════════════════════════════════════════════
# TEST CLASS 2 — record validator
# ══════════════════════════════════════════════════════════════════════════════

class TestRecordValidator(unittest.TestCase):

    def setUp(self):
        # Canonical valid record — individual tests modify a copy with {**...}
        self.valid = {"id": 1, "name": "Alice", "email": "alice@example.com"}

    def test_valid_record_passes(self):
        result = validate_record(self.valid)
        self.assertTrue(result.is_valid)
        self.assertIsNone(result.error)

    def test_id_zero_fails(self):
        result = validate_record({**self.valid, "id": 0})
        self.assertFalse(result.is_valid)
        self.assertIn("id", result.error)

    def test_negative_id_fails(self):
        result = validate_record({**self.valid, "id": -5})
        self.assertFalse(result.is_valid)

    def test_empty_name_fails(self):
        result = validate_record({**self.valid, "name": ""})
        self.assertFalse(result.is_valid)
        self.assertIn("name", result.error)

    def test_whitespace_only_name_fails(self):
        result = validate_record({**self.valid, "name": "   "})
        self.assertFalse(result.is_valid)

    def test_invalid_embedded_email_fails(self):
        result = validate_record({**self.valid, "email": "not-valid"})
        self.assertFalse(result.is_valid)

    def test_record_without_email_field_passes(self):
        """email is optional — record without it should still pass."""
        result = validate_record({"id": 2, "name": "Bob"})
        self.assertTrue(result.is_valid)

    def test_large_id_passes(self):
        result = validate_record({**self.valid, "id": 999_999_999})
        self.assertTrue(result.is_valid)


# ══════════════════════════════════════════════════════════════════════════════
# REFERENCE: key assertion methods
# ══════════════════════════════════════════════════════════════════════════════

def demo_assertion_methods() -> None:
    print("\n" + "═" * 78)
    print("  UNITTEST ASSERTION METHODS — REFERENCE")
    print("═" * 78)
    rows = [
        ("assertEqual(a, b)",          "a == b"),
        ("assertNotEqual(a, b)",       "a != b"),
        ("assertTrue(x)",              "bool(x) is True"),
        ("assertFalse(x)",             "bool(x) is False"),
        ("assertIsNone(x)",            "x is None"),
        ("assertIsNotNone(x)",         "x is not None"),
        ("assertIn(a, b)",             "a in b"),
        ("assertNotIn(a, b)",          "a not in b"),
        ("assertRaises(Exc, fn, ...)", "fn(...) raises Exc"),
        ("assertAlmostEqual(a, b, p)", "round(a-b, p) == 0"),
        ("subTest(msg, **kwargs)",     "label loop iterations — shows which case failed"),
    ]
    print(f"  {'Method':<38}  Checks")
    print(f"  {'-'*38}  {'-'*36}")
    for method, meaning in rows:
        print(f"  {method:<38}  {meaning}")
    print()
    print("  setUp()   → runs before every test method  (fresh object creation)")
    print("  tearDown()→ runs after every test method   (resource cleanup)")
    print()


def main() -> None:
    demo_assertion_methods()

    print("═" * 78)
    print("  RUNNING TESTS WITH unittest.TextTestRunner")
    print("═" * 78)
    print()

    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestEmailValidator))
    suite.addTests(loader.loadTestsFromTestCase(TestRecordValidator))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print()
    print(f"  Tests run : {result.testsRun}")
    print(f"  Failures  : {len(result.failures)}")
    print(f"  Errors    : {len(result.errors)}")
    print(f"  Skipped   : {len(result.skipped)}")
    print(f"  Status    : {'ALL PASSED' if result.wasSuccessful() else 'FAILURES DETECTED'}")


if __name__ == "__main__":
    main()

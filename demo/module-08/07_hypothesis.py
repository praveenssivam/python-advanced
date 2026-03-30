"""
07_hypothesis.py
================
Property-based testing with Hypothesis — let the framework find edge cases.

Topics:
  1. @given(st.text()) — Hypothesis generates 100+ random inputs automatically
  2. Testing invariants: idempotency, type safety
  3. Intentional bug: normalize_name_BUGGY fails on \\x00
     → Hypothesis finds and shrinks it to the minimal counterexample
  4. Fixed version: normalize_name (removes control chars)
  5. assume() — skip inputs that don't meet a precondition

Run:
    python demo/module-08/07_hypothesis.py
    pytest demo/module-08/07_hypothesis.py -v
"""

import sys
import unicodedata

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st


# ══════════════════════════════════════════════════════════════════════════════
# PRODUCTION CODE
# ══════════════════════════════════════════════════════════════════════════════

def normalize_name(name: str) -> str:
    """
    Normalizes a display name:
      - Remove Unicode control characters (category C: Cc, Cf, Co, Cs)
      - Collapse runs of whitespace to a single space
      - Title-case each word
      - Strip leading/trailing whitespace
    """
    cleaned = "".join(
        ch for ch in name
        if unicodedata.category(ch)[0] != "C"   # skip all control chars
    )
    return " ".join(cleaned.split()).title()


def normalize_name_BUGGY(name: str) -> str:
    """
    Intentionally buggy version: skips the control-character removal step.

    The property it breaks: "output must never contain control characters."
    Hypothesis will find '\\x00' (NULL) as the minimal failing input because
    '\\x00'.split() = ['\\x00'] (NULL is NOT Python whitespace) so it survives
    the join and appears in the output.

    The fixed normalize_name() removes all category-C chars first, so
    '\\x00' never appears in its output.
    """
    return " ".join(name.split()).title()


# ══════════════════════════════════════════════════════════════════════════════
# PART 1 — basic property tests (all pass)
# ══════════════════════════════════════════════════════════════════════════════

@given(st.text(min_size=0, max_size=200))
@settings(max_examples=200)
def test_normalize_always_returns_string(name):
    """Invariant: normalize_name never raises and always returns a str."""
    result = normalize_name(name)
    assert isinstance(result, str)


@given(st.text(min_size=0, max_size=200))
@settings(max_examples=200)
def test_normalize_name_is_idempotent(name):
    """
    Idempotency invariant: normalizing twice == normalizing once.
    Hypothesis tries 200 random Unicode strings to verify this holds for all.
    """
    once  = normalize_name(name)
    twice = normalize_name(once)
    assert once == twice


@given(
    st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Zs")),
        min_size=1,
        max_size=50,
    )
)
@settings(max_examples=100)
def test_normalize_letters_and_spaces_is_nonempty(name):
    """For inputs with only letters and spaces, output must be non-empty."""
    assume(name.strip())     # skip whitespace-only strings (assume = precondition)
    result = normalize_name(name)
    assert len(result) > 0


@given(st.emails())
@settings(max_examples=50)
def test_email_domain_lowercased(email):
    """Domain part of an email should be lowercased for normalization."""
    local, domain = email.rsplit("@", 1)
    normalized = f"{local}@{domain.lower()}"
    assert normalized.split("@")[1] == domain.lower()


# ══════════════════════════════════════════════════════════════════════════════
# PART 2 — bug demo (marked xfail so the CI stays green)
#
# Property under test: "output must never contain control characters."
# The BUGGY version fails this because '\x00'.isspace() == False, so
# split() keeps it; Hypothesis immediately shrinks to minimal input '\x00'.
#
# To SEE Hypothesis find and shrink the bug, run:
#   pytest demo/module-08/07_hypothesis.py::test_normalize_BUGGY_no_control_chars -v
#
# Hypothesis will output:
#   Falsifying example: test_normalize_BUGGY_no_control_chars(name='\x00')
#   AssertionError: control char '\x00' in output
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.xfail(
    reason="demonstrates Hypothesis finding a control-char preservation bug",
    strict=True,
)
@given(st.text(min_size=1, max_size=200))
@settings(max_examples=300)
def test_normalize_BUGGY_no_control_chars(name):
    """
    Invariant: a normalizer must remove ALL control characters from output.
    normalize_name_BUGGY omits the removal step:
      '\\x00'.isspace() == False → split() keeps it in the token list
      join + title → '\\x00' unchanged in output → assertion fails

    Hypothesis finds '\\x00' as the minimal counterexample and shrinks to it.

    The fixed normalize_name() strips all category-C chars first, so this
    invariant holds for every input Hypothesis can generate.

    Remove @xfail and run to see Hypothesis report the counterexample:
      pytest demo/module-08/07_hypothesis.py::test_normalize_BUGGY_no_control_chars -v
    """
    import unicodedata as _uc
    result = normalize_name_BUGGY(name)
    for ch in result:
        assert _uc.category(ch)[0] != "C", (
            f"control char {ch!r} (U+{ord(ch):04X}) found in output {result!r}"
        )


# ══════════════════════════════════════════════════════════════════════════════
# DEMO: Hypothesis concepts + manual shrinking walkthrough
# ══════════════════════════════════════════════════════════════════════════════

def demo_hypothesis_concepts() -> None:
    print("\n" + "═" * 78)
    print("  HYPOTHESIS — HOW IT WORKS")
    print("═" * 78)
    print()
    print("  @given(st.text(min_size=1))")
    print("  def test_my_property(s):")
    print("      once  = normalize_name(s)")
    print("      twice = normalize_name(once)")
    print("      assert once == twice          # invariant")
    print()
    print("  Hypothesis generates 100 examples by default (tune with @settings).")
    print("  On a failing example it SHRINKS — finds the minimal reproducing input:")
    print("    'A\\x00hello world!!' → 'A\\x00h' → 'A\\x00' → '\\x00'")
    print()
    print("  Key strategies:")
    rows = [
        ("st.text()",          "any Unicode string"),
        ("st.integers()",      "any integer"),
        ("st.emails()",        "valid email addresses"),
        ("st.dates()",         "valid date objects"),
        ("st.lists(...)",      "lists of the given strategy"),
        ("st.one_of(a, b)",    "union of two strategies"),
        ("st.fixed_dictionaries({...})", "dict with typed keys"),
    ]
    for strat, desc in rows:
        print(f"    {strat:<36}  {desc}")
    print()
    print("  assume(cond): skip this example if cond is False.")
    print("  Hypothesis will not count skipped examples toward max_examples.")
    print()


def demo_bug_shrinking() -> None:
    import unicodedata as _uc
    print("═" * 78)
    print("  MANUAL SHRINKING WALKTHROUGH — normalize_name_BUGGY")
    print("═" * 78)
    print()
    print("  Property: output must contain NO control characters.")
    print("  '\\x00'.isspace() == False  → split() keeps it  → BUG")
    print()
    test_cases = [
        "\x00",
        "\x00a",
        "\x01 Test",
        "Hello\x0cWorld",   # \x0c = form-feed IS whitespace → split removes it
        "Normal Name",      # control-free — no bug here
    ]
    print(f"  {'Input (repr)':<28}  {'Output (repr)':<28}  Has ctrl char?")
    print(f"  {'-'*28}  {'-'*28}  -------------")
    for tc in test_cases:
        out = normalize_name_BUGGY(tc)
        has_ctrl = any(_uc.category(ch)[0] == "C" for ch in out)
        flag = "YES  ← Hypothesis finds this" if has_ctrl else "no"
        print(f"  {repr(tc):<28}  {repr(out):<28}  {flag}")

    print()
    print("  Hypothesis shrinks to '\\x00' — the minimal failing input.")
    print("  Fixed normalize_name() strips all category-C chars first,")
    print("  so the 'no control chars in output' invariant holds for all inputs.")
    print()


def main() -> None:
    demo_hypothesis_concepts()
    demo_bug_shrinking()

    print("═" * 78)
    print("  RUNNING HYPOTHESIS TESTS")
    print("  (xfail test confirms the BUGGY version fails)")
    print("═" * 78)
    print()
    ret = pytest.main([__file__, "-v", "--tb=short", "--no-header"])
    sys.exit(ret)


if __name__ == "__main__":
    main()

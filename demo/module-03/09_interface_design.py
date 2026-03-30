"""
09_interface_design.py
========================
Two ways to define an interface in Python:
  1. Abstract Base Class (ABC) — explicit inheritance required.
  2. Protocol (PEP 544) — structural typing; no inheritance needed.

Both approaches work for type checking and polymorphism.
They have different trade-offs for library design, testing, and
working with third-party code.

Run:
    python demo/module-03/09_interface_design.py
"""

from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable


# ══════════════════════════════════════════════════════════════════════════════
# APPROACH 1: Abstract Base Class (ABC)
#
# Classes MUST explicitly inherit from the ABC and implement every
# @abstractmethod.  Forgetting any method → TypeError at instantiation.
#
# Strengths:
#   + Instantiation guard: can't accidentally create a broken subclass.
#   + isinstance() works naturally.
#   + Non-abstract helper methods are inherited for free.
#
# Limitations:
#   - Third-party classes can't satisfy the interface without inheriting.
#   - Creates a hard coupling between the ABC and every implementor.
#   - Not suitable for "duck typing" of outside code you don't control.
#
# Flow for ABCFormatter subclass:
#   1. Define class MyFormatter(ABCFormatter)
#   2. Implement format(rows) → string
#   3. Python checks at class-creation time: is format() defined?
#      Missing → error raised at MyFormatter() call
# ══════════════════════════════════════════════════════════════════════════════

class ABCFormatter(ABC):
    """Abstract formatter — explicit inheritance + abstractmethod enforcement."""

    @abstractmethod
    def format(self, rows: list[dict]) -> str:
        """Serialize rows into a string in this formatter's output format."""
        ...

    def preview(self, rows: list[dict], max_chars: int = 80) -> str:
        """Non-abstract helper — concrete subclasses inherit this for free."""
        output = self.format(rows)
        return output[:max_chars] + ("…" if len(output) > max_chars else "")


class CSVFormatterABC(ABCFormatter):
    """Concrete — inherits ABCFormatter, implements format()."""

    def format(self, rows: list[dict]) -> str:
        if not rows:
            return ""
        hdr = ",".join(rows[0].keys())
        body = [",".join(str(v) for v in r.values()) for r in rows]
        return "\n".join([hdr] + body)


class JSONFormatterABC(ABCFormatter):
    """Concrete — inherits ABCFormatter, implements format()."""

    def format(self, rows: list[dict]) -> str:
        import json
        return json.dumps(rows, separators=(",", ":"))


class IncompleteFormatterABC(ABCFormatter):
    """Forgot to implement format() — instantiation will raise TypeError."""
    pass


def render_report_abc(formatter: ABCFormatter, rows: list[dict]) -> None:
    """Accepts anything that inherits from ABCFormatter."""
    print(f"  [{type(formatter).__name__}] {formatter.preview(rows)}")


def demo_abc():
    print("=" * 60)
    print("APPROACH 1: ABC — explicit inheritance")
    print("=" * 60)
    print()

    rows = [{"city": "Mumbai", "count": 1200}, {"city": "Delhi", "count": 980}]

    # Flow: CSVFormatterABC() → Python checks all abstract methods → defined → OK
    for cls in (CSVFormatterABC, JSONFormatterABC):
        render_report_abc(cls(), rows)

    # Flow: IncompleteFormatterABC() → format() not defined → TypeError
    print()
    try:
        IncompleteFormatterABC()
    except TypeError as e:
        print(f"  IncompleteFormatterABC() raised TypeError: {e}")

    # ABC isinstance works
    fmt = CSVFormatterABC()
    print(f"\n  isinstance(CSVFormatterABC(), ABCFormatter) = {isinstance(fmt, ABCFormatter)}")


# ══════════════════════════════════════════════════════════════════════════════
# APPROACH 2: Protocol (structural typing, PEP 544)
#
# A Protocol defines the required SHAPE (method signatures) without
# requiring inheritance. Any class that has matching methods satisfies
# the protocol — even third-party classes or builtins.
#
# Strengths:
#   + Works with any class that has the right methods (duck typing).
#   + Zero coupling: third-party code satisfies it without modification.
#   + Ideal for type annotations in libraries.
#
# Limitations:
#   - No instantiation guard (no runtime error for missing methods).
#   - isinstance() only works if @runtime_checkable is added.
#   - No inherited helper methods.
#
# Flow for Protocol usage:
#   1. Define Protocol class with method stubs.
#   2. Write any class with matching signatures (no inherit needed).
#   3. Pass it to functions that accept the Protocol type.
#   → Static type checkers validate structural compatibility.
#   → @runtime_checkable enables isinstance() at runtime.
# ══════════════════════════════════════════════════════════════════════════════

@runtime_checkable
class FormatterProtocol(Protocol):
    """Structural interface: any class with a matching format() method qualifies."""

    def format(self, rows: list[dict]) -> str: ...


# ── Satisfies the Protocol without inheriting ────────────────────────────────

class TSVFormatter:
    """Satisfies FormatterProtocol by having a matching format() signature.

    It does NOT inherit from FormatterProtocol or ABCFormatter.
    A static type checker (mypy, pyright) will still accept it as a
    FormatterProtocol wherever that type is expected.
    """

    def format(self, rows: list[dict]) -> str:
        if not rows:
            return ""
        hdr = "\t".join(rows[0].keys())
        body = ["\t".join(str(v) for v in r.values()) for r in rows]
        return "\n".join([hdr] + body)


class MarkdownFormatter:
    """Another Protocol-satisfying class, no inheritance."""

    def format(self, rows: list[dict]) -> str:
        if not rows:
            return ""
        keys = list(rows[0].keys())
        sep = "| " + " | ".join("---" for _ in keys) + " |"
        lines = ["| " + " | ".join(keys) + " |", sep]
        for row in rows:
            lines.append("| " + " | ".join(str(row[k]) for k in keys) + " |")
        return "\n".join(lines)


def render_report_protocol(formatter: FormatterProtocol, rows: list[dict]) -> None:
    """Accepts any object with a matching format() method — no inheritance needed."""
    output = formatter.format(rows)
    print(f"  [{type(formatter).__name__}] {output[:80]}")


def demo_protocol():
    print("\n" + "=" * 60)
    print("APPROACH 2: Protocol — structural typing (duck typing)")
    print("=" * 60)
    print()

    rows = [{"city": "Mumbai", "count": 1200}, {"city": "Delhi", "count": 980}]

    # Flow: render_report_protocol(TSVFormatter(), rows)
    #   → calls formatter.format(rows)
    #   → TSVFormatter.format() runs — no inheritance, no issue
    for fmt_class in (TSVFormatter, MarkdownFormatter):
        render_report_protocol(fmt_class(), rows)

    # @runtime_checkable allows isinstance() check
    tsv = TSVFormatter()
    print(f"\n  isinstance(TSVFormatter(), FormatterProtocol) = {isinstance(tsv, FormatterProtocol)}")
    print(f"  isinstance(TSVFormatter(), ABCFormatter)      = {isinstance(tsv, ABCFormatter)}")


# ══════════════════════════════════════════════════════════════════════════════
# COMPARISON
# ══════════════════════════════════════════════════════════════════════════════

def demo_comparison():
    print("\n" + "=" * 60)
    print("Comparison: ABC vs. Protocol")
    print("=" * 60)
    print("""
  Feature                 ABC                     Protocol
  ──────────────────────  ──────────────────────  ─────────────────────────
  Requires inheritance?   Yes                     No
  Works with 3rd-party?   No (can't retrofit)     Yes (structural match)
  Instantiation guard?    Yes (TypeError)         No
  Inherited helpers?      Yes                     No
  isinstance() support?   Always                  With @runtime_checkable
  Best for                Library-internal hier.  Cross-codebase contracts
                          Enforced contracts      Testing fakes and mocks
    """)


def main():
    demo_abc()
    demo_protocol()
    demo_comparison()


if __name__ == "__main__":
    main()

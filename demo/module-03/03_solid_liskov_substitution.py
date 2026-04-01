"""
03_solid_liskov_substitution.py
=================================
Liskov Substitution Principle (LSP) — the L in SOLID.

A subclass must be usable wherever its parent is used.
It may add new behaviour, but must not change or break the parent's contract.

Run:
    python demo/module-03/03_solid_liskov_substitution.py
"""

from abc import ABC, abstractmethod


# ══════════════════════════════════════════════════════════════════════════════
# PART 1: VIOLATION — subclass breaks the parent's contract
#
# BaseExporter.export() is documented to return a string.
# ReadOnlyExporter.export() raises NotImplementedError instead.
#
# Any code that works with BaseExporter breaks when it gets a
# ReadOnlyExporter — the subclass can NOT substitute for the parent.
#
# LSP violation signs:
#   - isinstance() checks in calling code ("if it's ReadOnlyExporter, skip")
#   - try/except wrapping method calls to catch unexpected exceptions
#   - Docstring says "may raise" but parent says "always returns"
# ══════════════════════════════════════════════════════════════════════════════

class BaseExporter:
    """Parent contract: export(rows) always returns a non-empty string."""

    def export(self, rows: list[dict]) -> str:
        """Serialize rows to a string. Always returns a result — never raises."""
        headers = ",".join(rows[0].keys()) if rows else ""
        lines = [headers] + [",".join(str(v) for v in r.values()) for r in rows]
        return "\n".join(lines)


class ReadOnlyExporterBAD(BaseExporter):
    """BAD: Subclass breaks the parent contract by raising instead of returning.

    Calling code that expects any BaseExporter to work will unexpectedly fail
    when it receives a ReadOnlyExporter. This is an LSP violation.
    """

    def export(self, rows: list[dict]) -> str:
        raise NotImplementedError("ReadOnlyExporter cannot export data")  # ← violation


def run_export_pipeline(exporters: list[BaseExporter], rows: list[dict]) -> None:
    """Calling code written to BaseExporter's contract."""
    for exp in exporters:
        # This code holds to the contract: export() always returns a string.
        # It has no reason to expect an exception — but ReadOnlyExporterBAD breaks it.
        result = exp.export(rows)
        print(f"  {type(exp).__name__}: {len(result)} chars")


def demo_violation():
    print("=" * 60)
    print("PART 1: LSP Violation — subclass breaks parent contract")
    print("=" * 60)
    print()
    rows = [{"city": "Mumbai", "count": 1200}, {"city": "Delhi", "count": 980}]

    print("With well-behaved exporters (BaseExporter):")
    run_export_pipeline([BaseExporter()], rows)

    print("\nWith LSP-violating exporter in the mix:")
    try:
        # Flow: run_export_pipeline calls exp.export(rows) for each exporter
        #   → BaseExporter.export() → returns string   ✓
        #   → ReadOnlyExporterBAD.export() → raises NotImplementedError  ✗
        run_export_pipeline([BaseExporter(), ReadOnlyExporterBAD()], rows)
    except NotImplementedError as e:
        print(f"  Pipeline crashed: {e}")
    print()
    print("Calling code can't safely treat all exporters as interchangeable.")


# ══════════════════════════════════════════════════════════════════════════════
# PART 2: REFACTORED — correct hierarchy, no broken contracts
#
# The solution is to design the hierarchy correctly from the start:
#   - Exporter (ABC): defines the contract for writable exporters
#   - ReadOnlySource: a SEPARATE abstraction for sources that cannot export
#     (not a subtype of Exporter at all)
#   - CSVExporter, JSONExporter: proper subclasses — they ADD specialisation
#     but do not violate the parent contract.
#
# Rule: if D is a subtype of B, any property provable about B must hold for D.
#   Here: "export() returns a non-empty string" must hold for all Exporters.
# ══════════════════════════════════════════════════════════════════════════════

class Exporter(ABC):
    """Contract: export(rows) returns a string. Subclasses may specialise the
    format but must always return a result without raising.
    """

    @abstractmethod
    def export(self, rows: list[dict]) -> str:
        """Serialize rows. Returns non-empty string for non-empty input."""
        ...

    @property
    @abstractmethod
    def format_name(self) -> str:
        """Short label for the output format (e.g. 'csv', 'json')."""
        ...


class CSVExporter(Exporter):
    """Specialises Exporter for comma-separated output.

    Adds column-ordering behaviour, but still satisfies the parent contract:
    export() always returns a string.
    """

    format_name = "csv"

    def __init__(self, delimiter: str = ","):
        self._delim = delimiter

    def export(self, rows: list[dict]) -> str:
        # Flow: build header line → format each row → join with newlines
        if not rows:
            return ""
        headers = self._delim.join(rows[0].keys())
        lines = [headers] + [
            self._delim.join(str(v) for v in row.values()) for row in rows
        ]
        return "\n".join(lines)


class JSONExporter(Exporter):
    """Specialises Exporter for JSON output."""

    import json as _json
    format_name = "json"

    def export(self, rows: list[dict]) -> str:
        import json
        return json.dumps(rows, indent=2)


class MarkdownExporter(Exporter):
    """Specialises Exporter for Markdown table output.

    New subclass — no existing code modified to add this.
    """

    format_name = "markdown"

    def export(self, rows: list[dict]) -> str:
        if not rows:
            return ""
        keys = list(rows[0].keys())
        header = "| " + " | ".join(keys) + " |"
        separator = "| " + " | ".join("---" for _ in keys) + " |"
        lines = [header, separator]
        for row in rows:
            lines.append("| " + " | ".join(str(row[k]) for k in keys) + " |")
        return "\n".join(lines)


def run_pipeline(exporters: list[Exporter], rows: list[dict]) -> None:
    """Polymorphic usage — works with ANY concrete Exporter subclass."""
    for exp in exporters:
        # Flow: exp.export(rows) → always returns a string (LSP guaranteed)
        result = exp.export(rows)
        print(f"  [{exp.format_name:8s}] {len(result)} chars — first 60: {result[:60]!r}")


def demo_lsp():
    print("\n" + "=" * 60)
    print("PART 2: LSP Applied — subclasses honour the parent contract")
    print("=" * 60)
    print()
    rows = [{"city": "Mumbai", "count": 1200}, {"city": "Delhi", "count": 980}]

    # Flow: run_pipeline iterates exporters, calls export() on each
    #   → CSVExporter.export()      → returns CSV string ✓
    #   → JSONExporter.export()     → returns JSON string ✓
    #   → MarkdownExporter.export() → returns Markdown string ✓
    exporters: list[Exporter] = [
        CSVExporter(),
        CSVExporter(delimiter="\t"),  # specialisation: tab delimiter — still LSP-safe
        JSONExporter(),
        MarkdownExporter(),
    ]
    run_pipeline(exporters, rows)
    print()
    print("Any Exporter subclass can be passed to run_pipeline — no crashes,")
    print("no isinstance() checks needed. Each subclass adds formatting logic")
    print("without weakening the 'always returns a string' guarantee.")


def main():
    demo_violation()
    demo_lsp()


if __name__ == "__main__":
    main()

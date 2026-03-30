"""
06_inheritance_vs_composition.py
==================================
Demonstrates two design approaches:
  - Inheritance: a subclass IS a specialised version of the base class.
  - Composition: a class HAS a collaborating object that provides behaviour.

Domain: report generation with different output formats.

Run:
    python module-01/06_inheritance_vs_composition.py
"""


# ══════════════════════════════════════════════════════════════════════════════
# APPROACH 1: INHERITANCE
#
# ReportBase defines a template for generating reports.
# Subclasses specialise a PART (the _body) while inheriting the rest.
#
# When to use: the subclass truly IS a more specific version of the base,
# and the shared structure (header + body + footer) is stable.
#
# Flow for  CSVReport("Q1", data).generate():
#   1. generate() is inherited from ReportBase; calls self._header()
#   2. self._header() → ReportBase._header()  (not overridden) → "--- BEGIN ..."
#      Wait, ReportBase.generate() calls self._body():  → CSVReport._body()  (overridden!)
#   2. CSVReport._body(rows) → builds CSV header + lines
#   3. ReportBase._footer()  → "--- END ..."
#   4. return joined string
# ══════════════════════════════════════════════════════════════════════════════
# APPROACH 1: INHERITANCE
# ══════════════════════════════════════════════════════════════════════════════

class ReportBase:
    def __init__(self, title: str, rows: list[dict]):
        self.title = title
        self.rows = rows

    def generate(self) -> str:
        raise NotImplementedError("Subclasses must implement generate()")


class CSVReport(ReportBase):
    def generate(self) -> str:
        if not self.rows:
            return ""
        headers = ",".join(self.rows[0].keys())
        lines = [headers]
        for row in self.rows:
            lines.append(",".join(str(v) for v in row.values()))
        return "\n".join(lines)


class PlainTextReport(ReportBase):
    def generate(self) -> str:
        lines = [f"=== {self.title} ==="]
        for row in self.rows:
            lines.append("  " + " | ".join(f"{k}: {v}" for k, v in row.items()))
        return "\n".join(lines)


def demo_inheritance():
    print("=" * 50)
    print("APPROACH 1: Inheritance")
    print("=" * 50)

    data = [
        {"region": "North", "sales": 4200},
        {"region": "South", "sales": 3800},
    ]

    csv_report = CSVReport("Q1 Sales", data)
    txt_report = PlainTextReport("Q1 Sales", data)

    print("--- CSV ---")
    print(csv_report.generate())
    print("\n--- Plain Text ---")
    print(txt_report.generate())

    print()
    print("Observation: adding a new format (e.g., JSON) requires a new subclass.")
    print("The report logic and the formatting logic are coupled inside each class.")


# ══════════════════════════════════════════════════════════════════════════════
# APPROACH 2: COMPOSITION
#
# ReportService OWNS a formatter object — it does NOT inherit from a base.
# The formatter is injected at construction time (Dependency Injection).
# Adding a new format requires only a new formatter class; ReportService
# is never modified — it is closed for modification, open for extension.
#
# Flow for  ReportService(title, data, JSONFormatter()).generate():
#   1. __init__ stores self._formatter = JSONFormatter() instance
#   2. generate() calls self._formatter.format(self.title, self.rows)
#   3. JSONFormatter.format() → returns json.dumps({...})
#   4. ReportService knows nothing about JSON — it only calls .format()
#
# Flow for  service.switch_formatter(PlainTextFormatter()):
#   1. self._formatter is replaced at runtime
#   2. Next call to generate() uses PlainTextFormatter — no class changes
# ══════════════════════════════════════════════════════════════════════════════
# APPROACH 2: COMPOSITION
# ══════════════════════════════════════════════════════════════════════════════

class CSVFormatter:
    def format(self, title: str, rows: list[dict]) -> str:
        if not rows:
            return ""
        headers = ",".join(rows[0].keys())
        lines = [headers]
        for row in rows:
            lines.append(",".join(str(v) for v in row.values()))
        return "\n".join(lines)


class PlainTextFormatter:
    def format(self, title: str, rows: list[dict]) -> str:
        lines = [f"=== {title} ==="]
        for row in rows:
            lines.append("  " + " | ".join(f"{k}: {v}" for k, v in row.items()))
        return "\n".join(lines)


class JSONFormatter:
    """A third formatter added without touching ReportService."""
    import json as _json

    def format(self, title: str, rows: list[dict]) -> str:
        import json
        return json.dumps({"title": title, "rows": rows}, indent=2)


class ReportService:
    """Generates reports using an injected formatter.

    ReportService does not know or care what format is used — it delegates
    entirely to whatever formatter object was provided.
    """

    def __init__(self, title: str, rows: list[dict], formatter):
        self.title = title
        self.rows = rows
        self._formatter = formatter

    def generate(self) -> str:
        return self._formatter.format(self.title, self.rows)

    def switch_formatter(self, formatter) -> None:
        """Swap the formatter at runtime — no subclassing required."""
        self._formatter = formatter


def demo_composition():
    print("\n" + "=" * 50)
    print("APPROACH 2: Composition")
    print("=" * 50)

    data = [
        {"region": "North", "sales": 4200},
        {"region": "South", "sales": 3800},
    ]

    service = ReportService("Q1 Sales", data, formatter=CSVFormatter())
    print("--- CSV via composition ---")
    print(service.generate())

    # Swap formatter at runtime — no code change to ReportService
    service.switch_formatter(PlainTextFormatter())
    print("\n--- Plain Text after switch ---")
    print(service.generate())

    # Add a completely new format — ReportService is untouched
    service.switch_formatter(JSONFormatter())
    print("\n--- JSON after adding new formatter ---")
    print(service.generate())

    print()
    print("Observation: JSONFormatter was added without modifying ReportService.")
    print("Composition is more flexible when the 'what varies' can be isolated.")


# ══════════════════════════════════════════════════════════════════════════════
# COMPARISON NOTES
# ══════════════════════════════════════════════════════════════════════════════

def demo_comparison():
    print("\n" + "=" * 50)
    print("COMPARISON SUMMARY")
    print("=" * 50)
    print("""
  Inheritance                         Composition
  ─────────────────────────────────   ─────────────────────────────────────
  Subclass IS A base class            Class HAS A collaborating object
  Behaviour baked into the subclass   Behaviour injected from outside
  New format → new subclass           New format → new formatter class only
  Tighter coupling                    Looser coupling
  Good for genuine 'is-a' hierarchies Good for 'has-a' / 'uses-a' relations
  Harder to swap behaviour at runtime Easy to swap or mock
    """)


def main():
    demo_inheritance()
    demo_composition()
    demo_comparison()


if __name__ == "__main__":
    main()

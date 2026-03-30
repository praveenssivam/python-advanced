"""
07_method_overriding_and_abc.py
=================================
Demonstrates:
  - Overriding a method in a subclass
  - Using super() to extend (not replace) base behaviour
  - Abstract Base Classes (ABC) to define a required interface
  - @abstractmethod to enforce that subclasses implement specific methods

Domain: data exporters (CSV, JSON, Parquet).

Run:
    python module-01/07_method_overriding_and_abc.py
"""

from abc import ABC, abstractmethod
import json
import io


# ══════════════════════════════════════════════════════════════════════════════
# PART 1: Method overriding with super()
#
# When a subclass defines a method with the same name as a parent method,
# the subclass version REPLACES the parent for that class.
# super().<method>()  calls the parent's version explicitly, letting you
# EXTEND (add to) the parent behaviour rather than discard it.
#
# Python's method resolution searches the MRO (Method Resolution Order):
#   TSVExporter.__mro__ = [TSVExporter, BaseExporter, object]
#
# Flow for  TSVExporter().export(data):
#   1. export() → found on BaseExporter (not overridden in TSVExporter)
#      Calls self._header() → found on BaseExporter (not overridden) → "--- BEGIN ---"
#   2. Calls self._body(rows) → found on TSVExporter (OVERRIDDEN)  → tab-separated string
#   3. Calls self._footer()   → found on TSVExporter (OVERRIDDEN)  → calls super()._footer()
#      a. super()._footer() → BaseExporter._footer() → "--- END EXPORT ---"
#      b. returns "--- END EXPORT ---  [TSV format]"
# ══════════════════════════════════════════════════════════════════════════════
# PART 1: Method overriding with super()
# ══════════════════════════════════════════════════════════════════════════════

class BaseExporter:
    """Base exporter: wraps output with a header and footer."""

    def export(self, rows: list[dict]) -> str:
        header = self._header()
        body = self._body(rows)
        footer = self._footer()
        return f"{header}\n{body}\n{footer}"

    def _header(self) -> str:
        return "--- BEGIN EXPORT ---"

    def _body(self, rows: list[dict]) -> str:
        return "\n".join(str(row) for row in rows)

    def _footer(self) -> str:
        return "--- END EXPORT ---"


class TSVExporter(BaseExporter):
    """Overrides _body to produce tab-separated output.

    Calls super()._header() and super()._footer() unchanged.
    """

    def _body(self, rows: list[dict]) -> str:
        if not rows:
            return ""
        headers = "\t".join(rows[0].keys())
        lines = [headers]
        for row in rows:
            lines.append("\t".join(str(v) for v in row.values()))
        return "\n".join(lines)

    def _footer(self) -> str:
        # Extend the base footer rather than replace it entirely
        base_footer = super()._footer()
        return f"{base_footer}  [TSV format]"


def demo_overriding():
    print("=" * 50)
    print("PART 1: Method overriding and super()")
    print("=" * 50)

    data = [
        {"city": "Mumbai", "users": 1200},
        {"city": "Delhi",  "users": 980},
    ]

    base = BaseExporter()
    tsv = TSVExporter()

    print("-- BaseExporter --")
    print(base.export(data))

    print("\n-- TSVExporter (overrides _body, extends _footer) --")
    print(tsv.export(data))


# ══════════════════════════════════════════════════════════════════════════════
# PART 2: Abstract Base Classes — enforcing a contract
#
# ABC marks a class as abstract — it CANNOT be instantiated directly.
# @abstractmethod marks methods that EVERY concrete subclass MUST implement.
# If a subclass forgets to implement an @abstractmethod, Python raises
# TypeError at instantiation time (not at definition time).
#
# Flow for  Exporter():  (trying to instantiate the abstract base)
#   1. Python checks: does Exporter have any unimplemented @abstractmethods?
#   2. Yes: export() is @abstractmethod and not implemented on Exporter
#   3. Raise TypeError: "Can't instantiate abstract class Exporter
#      without an implementation for abstract method 'export'"
#
# Flow for  ParquetExporter():  (subclass that forgot export())
#   1. ParquetExporter inherits @abstractmethod export() from Exporter
#      and provides no implementation (only `pass`)
#   2. Python raises TypeError on instantiation — same guard as above
#
# Flow for  CSVExporter().export(data):  (correct subclass)
#   1. CSVExporter provides export() → no abstract methods remaining
#   2. Instantiation succeeds
#   3. export(data) → CSVExporter.export() → builds CSV string
# ══════════════════════════════════════════════════════════════════════════════
# PART 2: Abstract Base Classes — enforcing a contract
# ══════════════════════════════════════════════════════════════════════════════

class Exporter(ABC):
    """Contract: any concrete Exporter must implement export()."""

    @abstractmethod
    def export(self, rows: list[dict]) -> str:
        """Convert rows to an output string in this exporter's format."""
        ...

    def export_to_stream(self, rows: list[dict], stream: io.StringIO) -> None:
        """Non-abstract helper — subclasses get this for free."""
        stream.write(self.export(rows))


class CSVExporter(Exporter):
    def export(self, rows: list[dict]) -> str:
        if not rows:
            return ""
        headers = ",".join(rows[0].keys())
        lines = [headers] + [
            ",".join(str(v) for v in row.values()) for row in rows
        ]
        return "\n".join(lines)


class JSONExporter(Exporter):
    def export(self, rows: list[dict]) -> str:
        return json.dumps(rows, indent=2)


# ParquetExporter is declared but does NOT implement export() —
# instantiating it will raise TypeError.
class ParquetExporter(Exporter):
    pass  # forgot to implement export()


def demo_abc():
    print("\n" + "=" * 50)
    print("PART 2: Abstract Base Classes")
    print("=" * 50)

    data = [
        {"product": "widget", "qty": 50},
        {"product": "gadget", "qty": 20},
    ]

    # Concrete implementations work fine
    for cls in (CSVExporter, JSONExporter):
        exp = cls()
        print(f"\n-- {cls.__name__} --")
        print(exp.export(data))

    # Trying to instantiate Exporter directly raises TypeError
    print("\n-- Attempting to instantiate abstract Exporter directly --")
    try:
        Exporter()
    except TypeError as e:
        print(f"TypeError: {e}")

    # Trying to instantiate an incomplete subclass also raises TypeError
    print("\n-- Attempting to instantiate ParquetExporter (missing export()) --")
    try:
        ParquetExporter()
    except TypeError as e:
        print(f"TypeError: {e}")

    # Inherited non-abstract method works on concrete subclasses
    print("\n-- Using inherited export_to_stream() on CSVExporter --")
    buffer = io.StringIO()
    CSVExporter().export_to_stream(data, buffer)
    print(buffer.getvalue())


def main():
    demo_overriding()
    demo_abc()


if __name__ == "__main__":
    main()

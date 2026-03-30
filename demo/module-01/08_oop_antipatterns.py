"""
08_oop_antipatterns.py
========================
Demonstrates three common OOP anti-patterns, each followed by a
cleaner design. The bad and good versions are shown side-by-side
in the same file.

Anti-patterns covered:
  1. God Object — one class that knows and does everything
  2. Tight Coupling — classes that reach directly into each other's internals
  3. Inheritance Misuse — using inheritance purely for code reuse, not IS-A

Run:
    python module-01/08_oop_antipatterns.py
"""


# ══════════════════════════════════════════════════════════════════════════════
# ANTI-PATTERN 1: God Object
#
# A God Object is a class that holds too many responsibilities.
# Symptoms: enormous __init__, methods from 5 different domains,
# every change in the system touches this one class.
# Result: impossible to test in isolation, fragile when any part changes.
#
# Cure: identify each distinct responsibility and extract it into its own
# focused class.  The orchestrator becomes thin and delegates everything.
#
# Flow for DataPipeline.run("data/sales.csv"):
#   1. self._reader.read(source)        → CSVReader.read()       → list of raw dicts
#   2. self._validator.validate(raw)    → RowValidator.validate() → (clean, errors)
#   3. self._transformer.transform(clean) → MarkupTransformer.transform() → enriched list
#   4. return {"processed": result, "errors": errors}
#   Each step is testable independently; DataPipeline is unchanged when any step changes.
# ══════════════════════════════════════════════════════════════════════════════
# ANTI-PATTERN 1: God Object
# A single class accumulates too many responsibilities.
# Signs: huge __init__, methods from 5 different domains, hard to test.
# ══════════════════════════════════════════════════════════════════════════════

class DataPipelineGod:
    """BAD: One class handles ingestion, validation, transformation,
    persistence, and reporting. Adding anything here makes it worse.
    """

    def __init__(self, source_path: str, destination: str):
        self.source_path = source_path
        self.destination = destination
        self.raw_data = []
        self.clean_data = []
        self.errors = []

    def read_csv(self):
        # Imagine file I/O here
        self.raw_data = [{"id": 1, "amount": "1200"}, {"id": 2, "amount": "bad"}]

    def validate(self):
        for row in self.raw_data:
            try:
                float(row["amount"])
                self.clean_data.append(row)
            except ValueError:
                self.errors.append(row)

    def transform(self):
        for row in self.clean_data:
            row["amount"] = float(row["amount"]) * 1.1  # apply 10% markup

    def save_to_db(self):
        # Imagine DB writes here
        pass

    def send_email_report(self):
        # Email logic mixed into the pipeline class
        pass

    def generate_pdf(self):
        # PDF generation also in the same class
        pass


# GOOD: Split into focused collaborators

class CSVReader:
    def read(self, path: str) -> list[dict]:
        # Simplified — returns simulated data
        return [{"id": 1, "amount": "1200"}, {"id": 2, "amount": "bad"}]


class RowValidator:
    def validate(self, rows: list[dict]) -> tuple[list[dict], list[dict]]:
        clean, errors = [], []
        for row in rows:
            try:
                float(row["amount"])
                clean.append(row)
            except ValueError:
                errors.append(row)
        return clean, errors


class MarkupTransformer:
    def __init__(self, pct: float = 10):
        self.multiplier = 1 + pct / 100

    def transform(self, rows: list[dict]) -> list[dict]:
        return [{**row, "amount": float(row["amount"]) * self.multiplier} for row in rows]


class DataPipeline:
    """GOOD: Thin orchestrator that delegates to focused components."""

    def __init__(self, reader, validator, transformer):
        self._reader = reader
        self._validator = validator
        self._transformer = transformer

    def run(self, source: str) -> dict:
        raw = self._reader.read(source)
        clean, errors = self._validator.validate(raw)
        result = self._transformer.transform(clean)
        return {"processed": result, "errors": errors}


def demo_god_object():
    print("=" * 50)
    print("ANTI-PATTERN 1: God Object  →  Focused Collaborators")
    print("=" * 50)

    print("BAD: DataPipelineGod has read, validate, transform, save, email, PDF.")
    print("     Every change risks breaking unrelated functionality.")

    pipeline = DataPipeline(
        reader=CSVReader(),
        validator=RowValidator(),
        transformer=MarkupTransformer(pct=10),
    )
    result = pipeline.run("data/sales.csv")
    print(f"\nGOOD: DataPipeline result:")
    print(f"  Processed rows : {result['processed']}")
    print(f"  Error rows     : {result['errors']}")
    print("Each component can be tested, swapped, or evolved independently.")


# ══════════════════════════════════════════════════════════════════════════════
# ANTI-PATTERN 2: Tight Coupling
#
# Tight coupling happens when one class reaches DIRECTLY into another class's
# internals — reading or writing private attributes, or making assumptions
# about implementation details that could change.
#
# Cure: communicate via a PUBLIC METHOD INTERFACE instead.
# The caller asks the other object for the behaviour it needs; it doesn’t
# manipulate the data directly.
#
# Flow for  InvoiceTight.generate(bad_order)  (BAD):
#   1. invoice directly sets  bad_order.discount = 5  → MUTATES caller's data!
#   2. Reads bad_order.items directly  → relies on internal structure
#   3. Side-effect: subsequent calls see a permanently mutated Order
#
# Flow for  Invoice.generate(good_order)  (GOOD):
#   1. invoice calls  good_order.total()  → asks Order to compute its own total
#   2. Order.total() reads self._items and self._discount internally
#   3. Invoice never touches Order's internals — no mutation, no coupling
# ══════════════════════════════════════════════════════════════════════════════
# ANTI-PATTERN 2: Tight Coupling
# One class directly accesses or modifies another class's internals.
# ══════════════════════════════════════════════════════════════════════════════

class OrderTight:
    def __init__(self, items: list):
        self.items = items
        self.discount = 0  # exposed raw attribute


class InvoiceTight:
    """BAD: Directly reads and modifies Order's internal state."""

    def generate(self, order: OrderTight) -> str:
        # Reaches into order's internals and modifies them
        order.discount = 5  # side-effect: mutates the order!
        total = sum(i["price"] for i in order.items) - order.discount
        return f"Invoice total: ${total:.2f} (discount ${order.discount} applied)"


class Order:
    def __init__(self, items: list, discount: float = 0):
        self._items = items
        self._discount = discount

    def total(self) -> float:
        return sum(i["price"] for i in self._items) - self._discount

    def apply_discount(self, amount: float) -> None:
        self._discount = amount


class Invoice:
    """GOOD: Asks Order for its total — does not touch Order's internals."""

    def generate(self, order: Order) -> str:
        return f"Invoice total: ${order.total():.2f}"


def demo_tight_coupling():
    print("\n" + "=" * 50)
    print("ANTI-PATTERN 2: Tight Coupling  →  Communicate via Interface")
    print("=" * 50)

    items = [{"name": "widget", "price": 100}, {"name": "gadget", "price": 50}]

    bad_order = OrderTight(items)
    invoice_bad = InvoiceTight()
    print(f"BAD: {invoice_bad.generate(bad_order)}")
    print(f"     order.discount mutated to: {bad_order.discount}  ← side-effect!")

    good_order = Order(items)
    good_order.apply_discount(5)
    invoice_good = Invoice()
    print(f"\nGOOD: {invoice_good.generate(good_order)}")
    print("      Invoice reads total via a method — Order owns its own state.")


# ══════════════════════════════════════════════════════════════════════════════
# ANTI-PATTERN 3: Inheritance Misuse
#
# Inheritance models an IS-A relationship: a Dog IS-A Animal.
# Misuse: inheriting from a class ONLY to reuse one of its methods,
# even when the IS-A relationship makes no semantic sense.
# This creates misleading type hierarchies and causes `isinstance()` to lie.
#
# Cure: prefer COMPOSITION over inheritance for code reuse.
# "Has-a" / "Uses-a" relationships should be expressed through a contained
# object, not by extending a base class.
#
# Flow for  UserReport.generate(users)  (BAD):
#   1. UserReport inherits from CSVWriterBase
#   2. Calling isinstance(report, CSVWriterBase) → True  (misleading!)
#   3. CSVWriterBase.write_csv() is reused, but UserReport IS NOT a CSVWriterBase
#
# Flow for  UserReportGood.generate(users)  (GOOD):
#   1. UserReportGood stores a writer callable: self._write
#   2. generate() calls self._write(users, "users.csv")
#   3. The writer can be swapped without changing UserReportGood
#   4. isinstance(report, CSVWriterBase) → False (correctly, there's no IS-A)
# ══════════════════════════════════════════════════════════════════════════════
# ANTI-PATTERN 3: Inheritance Misuse
# Inheriting from a class just to reuse a method, even when the IS-A
# relationship makes no semantic sense.
# ══════════════════════════════════════════════════════════════════════════════

class CSVWriterBase:
    def write_csv(self, rows: list[dict], path: str) -> str:
        headers = ",".join(rows[0].keys()) if rows else ""
        lines = [headers] + [",".join(str(v) for v in r.values()) for r in rows]
        return "\n".join(lines)


class UserReport(CSVWriterBase):
    """BAD: Inherits from CSVWriterBase only to reuse write_csv.
    A UserReport IS NOT a CSVWriterBase — this is inheritance for convenience.
    """

    def generate(self, users: list[dict]) -> str:
        return self.write_csv(users, "users.csv")


class UserReportGood:
    """GOOD: Uses composition — holds a reference to a writer callable."""

    def __init__(self, writer=None):
        self._write = writer or self._default_write

    def _default_write(self, rows: list[dict], path: str) -> str:
        headers = ",".join(rows[0].keys()) if rows else ""
        lines = [headers] + [",".join(str(v) for v in r.values()) for r in rows]
        return "\n".join(lines)

    def generate(self, users: list[dict]) -> str:
        return self._write(users, "users.csv")


def demo_inheritance_misuse():
    print("\n" + "=" * 50)
    print("ANTI-PATTERN 3: Inheritance Misuse  →  Composition for Reuse")
    print("=" * 50)

    users = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]

    bad_report = UserReport()
    print("BAD (inheritance for reuse):")
    print(bad_report.generate(users))
    print("  UserReport inherits from CSVWriterBase but IS NOT a CSVWriterBase.")
    print("  This makes isinstance/type checks and future refactoring misleading.")

    good_report = UserReportGood()
    print("\nGOOD (composition for reuse):")
    print(good_report.generate(users))
    print("  UserReportGood uses a writer internally. The writer is replaceable.")


def main():
    demo_god_object()
    demo_tight_coupling()
    demo_inheritance_misuse()


if __name__ == "__main__":
    main()

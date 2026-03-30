"""
01_solid_single_responsibility.py
====================================
Single Responsibility Principle (SRP) — the S in SOLID.

Problem:  One class accumulates multiple responsibilities.
Solution: Split into focused classes, each with one reason to change.

Run:
    python demo/module-03/01_solid_single_responsibility.py
"""


# ══════════════════════════════════════════════════════════════════════════════
# PART 1: VIOLATION — one class does it all
#
# DataPipelineProcessor reads CSV, validates rows, transforms them,
# logs errors, AND writes to storage — all in one place.
#
# Why this hurts:
#   - A logging format change forces you to touch the ETL logic.
#   - A storage engine swap forces you to touch the validator.
#   - No unit can be tested in isolation.
#   - Every new requirement inflates the same class further.
# ══════════════════════════════════════════════════════════════════════════════

class DataPipelineProcessorBAD:
    """BAD: reads, validates, transforms, logs, and stores all in one class.

    Any change to any responsibility (logging format, storage engine,
    validation rules, transformation logic) requires modifying this class.
    With five concerns interleaved, testing any one of them in isolation
    is nearly impossible.
    """

    def __init__(self, source: str, dest: str):
        self.source = source
        self.dest = dest
        self._log: list[str] = []

    # ── Responsibility 1: CSV reading ────────────────────────────────────────
    def read_csv(self) -> list[dict]:
        # Simulated — in real code this would open a file
        return [
            {"id": "1", "amount": "1200", "region": "north"},
            {"id": "2", "amount": "bad",  "region": "south"},
            {"id": "3", "amount": "800",  "region": ""},
        ]

    # ── Responsibility 2: Validation ─────────────────────────────────────────
    def validate(self, rows: list[dict]) -> tuple[list[dict], list[dict]]:
        clean, errors = [], []
        for row in rows:
            try:
                float(row["amount"])
                if not row["region"]:
                    raise ValueError("region is empty")
                clean.append(row)
            except (ValueError, KeyError) as e:
                self._log.append(f"[VALIDATE] Row {row.get('id')} failed: {e}")
                errors.append(row)
        return clean, errors

    # ── Responsibility 3: Transformation ─────────────────────────────────────
    def transform(self, rows: list[dict]) -> list[dict]:
        return [{**row, "amount": float(row["amount"]) * 1.1} for row in rows]

    # ── Responsibility 4: Logging ─────────────────────────────────────────────
    def flush_log(self) -> None:
        for entry in self._log:
            print(f"  LOG: {entry}")
        self._log.clear()

    # ── Responsibility 5: Storage ─────────────────────────────────────────────
    def save(self, rows: list[dict]) -> None:
        # Simulated write
        print(f"  SAVE: {len(rows)} rows → {self.dest}")

    def run(self) -> None:
        raw = self.read_csv()
        clean, _ = self.validate(raw)
        transformed = self.transform(clean)
        self.flush_log()
        self.save(transformed)


def demo_violation():
    print("=" * 60)
    print("PART 1: SRP Violation — one class, five responsibilities")
    print("=" * 60)
    print()
    print("DataPipelineProcessorBAD.run():")
    print()
    processor = DataPipelineProcessorBAD("data/sales.csv", "db/clean")
    processor.run()
    print()
    print("Problem: changing the log format, swap storage engine, or add")
    print("a new validation rule all require touching the SAME class.")
    print("None of these components can be tested or reused in isolation.")


# ══════════════════════════════════════════════════════════════════════════════
# PART 2: REFACTORED — one class, one reason to change
#
# Each class now owns exactly one concern:
#
#   CSVReader        → knows how to read rows from a CSV source
#   RowValidator     → knows what makes a row valid
#   MarkupTransformer→ knows how to apply a business transformation
#   PipelineLogger   → knows how to record and emit log entries
#   RowStore         → knows how to persist rows
#   Pipeline         → knows how to orchestrate the above (thin coordinator)
#
# To change logging format:   edit PipelineLogger only.
# To add a validation rule:   edit RowValidator only.
# To swap the storage engine: replace RowStore only.
# The Pipeline coordinator never changes for these reasons.
# ══════════════════════════════════════════════════════════════════════════════

class CSVReader:
    """Responsibility: read rows from a CSV-like source."""

    def read(self, source: str) -> list[dict]:
        """Return raw rows from source. In real use: open file, parse CSV."""
        # Simulated
        return [
            {"id": "1", "amount": "1200", "region": "north"},
            {"id": "2", "amount": "bad",  "region": "south"},
            {"id": "3", "amount": "800",  "region": ""},
        ]


class RowValidator:
    """Responsibility: decide whether a row is valid.

    Returns (clean_rows, error_rows). Does not log, does not transform.
    """

    def validate(self, rows: list[dict]) -> tuple[list[dict], list[dict]]:
        clean, errors = [], []
        for row in rows:
            try:
                float(row["amount"])
                if not row.get("region"):
                    raise ValueError("region is empty")
                clean.append(row)
            except (ValueError, KeyError):
                errors.append(row)
        return clean, errors


class MarkupTransformer:
    """Responsibility: apply a percentage markup to the 'amount' field."""

    def __init__(self, pct: float = 10.0):
        self._multiplier = 1 + pct / 100

    def transform(self, rows: list[dict]) -> list[dict]:
        """Return new rows with amount increased by markup %. Input is unchanged."""
        return [{**row, "amount": float(row["amount"]) * self._multiplier} for row in rows]


class PipelineLogger:
    """Responsibility: accumulate log entries and emit them on demand."""

    def __init__(self):
        self._entries: list[str] = []

    def log(self, message: str) -> None:
        self._entries.append(message)

    def flush(self) -> None:
        for e in self._entries:
            print(f"  LOG: {e}")
        self._entries.clear()


class RowStore:
    """Responsibility: persist rows to a destination."""

    def save(self, rows: list[dict], dest: str) -> None:
        print(f"  SAVE: {len(rows)} rows → {dest}")


class Pipeline:
    """Responsibility: orchestrate collaborators in the correct order.

    Pipeline itself does not know how reading, validation, transformation,
    logging, or storage work — that knowledge lives in the collaborators.
    Swapping any collaborator never touches this class.
    """

    def __init__(
        self,
        reader: CSVReader,
        validator: RowValidator,
        transformer: MarkupTransformer,
        logger: PipelineLogger,
        store: RowStore,
    ):
        self._reader = reader
        self._validator = validator
        self._transformer = transformer
        self._logger = logger
        self._store = store

    def run(self, source: str, dest: str) -> None:
        # Flow: read → validate → log errors → transform → save
        raw = self._reader.read(source)

        clean, errors = self._validator.validate(raw)
        for row in errors:
            self._logger.log(f"Row {row.get('id')} rejected: invalid amount or empty region")

        result = self._transformer.transform(clean)
        self._logger.flush()
        self._store.save(result, dest)


def demo_srp():
    print("\n" + "=" * 60)
    print("PART 2: SRP Applied — each class has one job")
    print("=" * 60)
    print()
    print("Pipeline.run() with focused collaborators:")
    print()

    # Flow: Pipeline(reader, validator, transformer, logger, store)
    #   → reader.read()          yields raw rows
    #   → validator.validate()   splits clean vs. errors
    #   → logger.log()           records each error
    #   → transformer.transform() raises amounts by 10%
    #   → logger.flush()         prints all log entries
    #   → store.save()           writes result rows
    pipeline = Pipeline(
        reader=CSVReader(),
        validator=RowValidator(),
        transformer=MarkupTransformer(pct=10),
        logger=PipelineLogger(),
        store=RowStore(),
    )
    pipeline.run("data/sales.csv", "db/clean")

    print()
    print("Each class can now be tested and replaced in isolation:")
    print("  RowValidator  — unit-testable with no I/O or side effects")
    print("  PipelineLogger— swap to JSON logs by replacing one class")
    print("  RowStore      — swap to S3 by replacing one class")


def main():
    demo_violation()
    demo_srp()


if __name__ == "__main__":
    main()

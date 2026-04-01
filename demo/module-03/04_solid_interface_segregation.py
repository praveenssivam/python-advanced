"""
04_solid_interface_segregation.py
====================================
Interface Segregation Principle (ISP) — the I in SOLID.

Problem:  One large interface forces all implementors to define methods
          they don't use.
Solution: Split into small, focused interfaces. Clients depend only on
          the methods they actually need.

Run:
    python demo/module-03/04_solid_interface_segregation.py
"""

from abc import ABC, abstractmethod


# ══════════════════════════════════════════════════════════════════════════════
# PART 1: VIOLATION — fat interface forces unused method stubs
#
# IDataConnector declares five capabilities.
# A read-only connector (S3ReadConnector) must implement write_records()
# and delete_records() even though it will never use them — or raise
# NotImplementedError, breaking LSP as a side effect.
#
# Why this hurts:
#   - Every new connector must stub out methods it cannot support.
#   - Calling code that type-checks against IDataConnector cannot know
#     which methods are actually safe to call without reading the subclass.
#   - Adding a new method to IDataConnector forces ALL implementors to update.
# ══════════════════════════════════════════════════════════════════════════════

class IDataConnectorFat(ABC):
    """BAD: single interface for read, write, schema, stats, and delete.

    An S3 read-only connector must still implement write_records and
    delete_records — but those operations make no sense for it.
    """

    @abstractmethod
    def connect(self) -> None: ...

    @abstractmethod
    def read_records(self, query: str) -> list[dict]: ...

    @abstractmethod
    def write_records(self, records: list[dict]) -> int: ...

    @abstractmethod
    def delete_records(self, condition: str) -> int: ...

    @abstractmethod
    def get_schema(self, table: str) -> dict: ...


class S3ReadConnectorBAD(IDataConnectorFat):
    """BAD: forced to stub write/delete even though S3 bucket is read-only here."""

    def connect(self) -> None:
        print("  [S3ReadConnector] connected to s3://my-bucket")

    def read_records(self, query: str) -> list[dict]:
        return [{"id": 1, "value": "abc"}]

    def write_records(self, records: list[dict]) -> int:
        raise NotImplementedError("This connector is read-only")  # ← forced stub

    def delete_records(self, condition: str) -> int:
        raise NotImplementedError("This connector is read-only")  # ← forced stub

    def get_schema(self, table: str) -> dict:
        return {"id": "integer", "value": "string"}


def demo_violation():
    print("=" * 60)
    print("PART 1: ISP Violation — fat interface, forced stubs")
    print("=" * 60)
    print()
    conn = S3ReadConnectorBAD()
    conn.connect()
    rows = conn.read_records("SELECT * FROM raw")
    print(f"  read_records → {rows}")
    try:
        conn.write_records([{"id": 2}])
    except NotImplementedError as e:
        print(f"  write_records → NotImplementedError: {e}")
    print()
    print("S3ReadConnectorBAD was forced to implement 2 methods it can't support.")
    print("Any caller holding IDataConnectorFat can't safely call write/delete.")


# ══════════════════════════════════════════════════════════════════════════════
# PART 2: REFACTORED — small, focused interfaces
#
# Split IDataConnectorFat into four separate interfaces:
#
#   IConnectable     → connect() only
#   IReadable        → read_records() only
#   IWritable        → write_records() only
#   ISchemaProvider  → get_schema() only
#
# Concrete classes implement only the interfaces they can fulfil.
# Clients declare precisely what they need:
#   - A read pipeline: IConnectable + IReadable
#   - A write pipeline: IConnectable + IWritable
#   - A schema inspector: ISchemaProvider
# ══════════════════════════════════════════════════════════════════════════════

class IConnectable(ABC):
    """Can establish a connection."""

    @abstractmethod
    def connect(self) -> None: ...


class IReadable(ABC):
    """Can read records given a query string."""

    @abstractmethod
    def read_records(self, query: str) -> list[dict]: ...


class IWritable(ABC):
    """Can write a batch of records, returning the count written."""

    @abstractmethod
    def write_records(self, records: list[dict]) -> int: ...


class ISchemaProvider(ABC):
    """Can describe the schema of a named table."""

    @abstractmethod
    def get_schema(self, table: str) -> dict: ...


# ── Read-only connector — only implements what it supports ───────────────────

class S3ReadConnector(IConnectable, IReadable, ISchemaProvider):
    """Read-only S3 connector — does NOT implement IWritable (and doesn't have to)."""

    def connect(self) -> None:
        print("  [S3ReadConnector] connected to s3://my-bucket")

    def read_records(self, query: str) -> list[dict]:
        return [{"id": 1, "value": "abc"}, {"id": 2, "value": "def"}]

    def get_schema(self, table: str) -> dict:
        return {"id": "integer", "value": "string"}


# ── Read/write connector — implements the full surface it supports ────────────

class PostgresConnector(IConnectable, IReadable, IWritable, ISchemaProvider):
    """Full-featured Postgres connector — read, write, and schema."""

    def connect(self) -> None:
        print("  [PostgresConnector] connected to postgres://localhost/lab")

    def read_records(self, query: str) -> list[dict]:
        return [{"id": 1, "value": "row1"}, {"id": 2, "value": "row2"}]

    def write_records(self, records: list[dict]) -> int:
        print(f"  [PostgresConnector] writing {len(records)} records")
        return len(records)

    def get_schema(self, table: str) -> dict:
        return {"id": "serial", "value": "varchar(255)"}


# ── Client functions depend only on the interfaces they use ──────────────────

def run_read_pipeline(source: IConnectable | IReadable) -> list[dict]:
    """Needs only connect + read — does not know about write or schema."""
    # Flow: source.connect() → source.read_records() → return rows
    source.connect()
    return source.read_records("SELECT * FROM data")


def inspect_schema(provider: ISchemaProvider, table: str) -> None:
    """Needs only schema info — does not care about read or write ability."""
    schema = provider.get_schema(table)
    print(f"  Schema for {table!r}: {schema}")


def run_write_pipeline(dest: IConnectable | IWritable, records: list[dict]) -> int:
    """Needs only connect + write."""
    dest.connect()
    return dest.write_records(records)


def demo_isp():
    print("\n" + "=" * 60)
    print("PART 2: ISP Applied — small interfaces, no forced stubs")
    print("=" * 60)
    print()
    rows = [{"id": 10, "value": "new_record"}]

    print("S3ReadConnector — read + schema only:")
    s3 = S3ReadConnector()
    result = run_read_pipeline(s3)
    print(f"  read_records → {result}")
    inspect_schema(s3, "raw_data")

    print()
    print("PostgresConnector — read + write + schema:")
    pg = PostgresConnector()
    result = run_read_pipeline(pg)
    print(f"  read_records → {result}")
    count = run_write_pipeline(pg, rows)
    print(f"  write_records → {count} row(s) written")
    inspect_schema(pg, "clean_data")

    print()
    print("S3ReadConnector is never forced to pretend it can write.")
    print("Each client function only depends on the interface it needs.")


def main():
    demo_violation()
    demo_isp()


if __name__ == "__main__":
    main()

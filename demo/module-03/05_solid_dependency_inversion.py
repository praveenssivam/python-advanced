"""
05_solid_dependency_inversion.py
===================================
Dependency Inversion Principle (DIP) — the D in SOLID.

Problem:  High-level module directly instantiates its concrete dependencies.
          Swapping an implementation requires editing the high-level class.
Solution: High-level module depends on abstractions (ABCs). Concrete
          implementations are injected from outside.

Run:
    python demo/module-03/05_solid_dependency_inversion.py
"""

from abc import ABC, abstractmethod


# ══════════════════════════════════════════════════════════════════════════════
# PART 1: VIOLATION — high-level class hard-wires concrete dependencies
#
# PipelineRunnerBAD creates its own FileLogger and SQLiteStorage inside
# __init__. To test PipelineRunnerBAD in isolation, or to swap to a
# cloud storage engine, you must edit PipelineRunnerBAD itself.
#
# Both the high-level class (PipelineRunner) AND the concrete dependencies
# (FileLogger, SQLiteStorage) are "concrete" — nobody depends on an
# abstraction. This is the inversion that DIP asks us to make.
# ══════════════════════════════════════════════════════════════════════════════

class FileLoggerConcrete:
    def log(self, message: str) -> None:
        print(f"  [FileLogger] {message}")


class SQLiteStorageConcrete:
    def save(self, records: list[dict]) -> int:
        print(f"  [SQLiteStorage] saving {len(records)} records to sqlite")
        return len(records)


class PipelineRunnerBAD:
    """BAD: instantiates FileLogger and SQLiteStorage directly.

    To switch to CloudLogger or S3Storage: edit this class.
    To unit-test without file I/O or DB: impossible without monkey-patching.
    """

    def __init__(self):
        self._logger = FileLoggerConcrete()       # ← hard-coded concrete type
        self._storage = SQLiteStorageConcrete()   # ← hard-coded concrete type

    def run(self, records: list[dict]) -> int:
        self._logger.log(f"Running pipeline with {len(records)} records")
        count = self._storage.save(records)
        self._logger.log(f"Done — {count} records saved")
        return count


def demo_violation():
    print("=" * 60)
    print("PART 1: DIP Violation — high-level class owns its dependencies")
    print("=" * 60)
    print()
    runner = PipelineRunnerBAD()
    runner.run([{"id": 1}, {"id": 2}])
    print()
    print("To swap FileLogger → CloudLogger: must edit PipelineRunnerBAD.")
    print("To swap SQLiteStorage → S3Storage: same edit, same risk.")


# ══════════════════════════════════════════════════════════════════════════════
# PART 2: REFACTORED — depend on abstractions, not on implementations
#
# ILogger and IStorage are abstract interfaces.
# PipelineRunner accepts them from outside (constructor injection).
#
# Dependency direction:
#   PipelineRunner → ILogger       (abstraction)
#   PipelineRunner → IStorage      (abstraction)
#   FileLogger     → ILogger       (implements)
#   CloudLogger    → ILogger       (implements — added without touching runner)
#   SQLiteStorage  → IStorage      (implements)
#   S3Storage      → IStorage      (implements — added without touching runner)
#
# Flow for PipelineRunner.run(records):
#   1. self._logger.log("running...")   ← calls abstract interface
#   2. count = self._storage.save(...)  ← calls abstract interface
#   3. self._logger.log("done")
#   Concrete implementations determine what actually happens.
# ══════════════════════════════════════════════════════════════════════════════

class ILogger(ABC):
    """Abstraction: anything that can accept a string log message."""

    @abstractmethod
    def log(self, message: str) -> None: ...


class IStorage(ABC):
    """Abstraction: anything that can persist a batch of records."""

    @abstractmethod
    def save(self, records: list[dict]) -> int:
        """Persist records; return count of records saved."""
        ...


# ── Concrete implementations of ILogger ─────────────────────────────────────

class FileLogger(ILogger):
    def log(self, message: str) -> None:
        print(f"  [FileLogger]  {message}")


class CloudLogger(ILogger):
    """A new logger added without touching PipelineRunner."""

    def __init__(self, service: str = "CloudWatch"):
        self._service = service

    def log(self, message: str) -> None:
        print(f"  [CloudLogger:{self._service}]  {message}")


class SilentLogger(ILogger):
    """Discards all messages — useful in tests."""

    def log(self, message: str) -> None:
        pass


# ── Concrete implementations of IStorage ────────────────────────────────────

class SQLiteStorage(IStorage):
    def save(self, records: list[dict]) -> int:
        print(f"  [SQLiteStorage] saving {len(records)} records to sqlite")
        return len(records)


class S3Storage(IStorage):
    """A new storage engine added without touching PipelineRunner."""

    def __init__(self, bucket: str):
        self._bucket = bucket

    def save(self, records: list[dict]) -> int:
        print(f"  [S3Storage]     uploading {len(records)} records → s3://{self._bucket}")
        return len(records)


class InMemoryStorage(IStorage):
    """Stores records in a list — useful in tests (no I/O)."""

    def __init__(self):
        self.records: list[dict] = []

    def save(self, records: list[dict]) -> int:
        self.records.extend(records)
        return len(records)


# ── High-level module — depends only on abstractions ────────────────────────

class PipelineRunner:
    """Orchestrates a pipeline using injected ILogger and IStorage.

    PipelineRunner never changes when a new logger or storage type is added.
    The concrete choice is made by the caller (the composition root).
    """

    def __init__(self, logger: ILogger, storage: IStorage):
        self._logger = logger
        self._storage = storage

    def run(self, records: list[dict]) -> int:
        # Flow: log → save → log
        self._logger.log(f"Running pipeline with {len(records)} records")
        count = self._storage.save(records)
        self._logger.log(f"Done — {count} records saved")
        return count


def demo_dip():
    print("\n" + "=" * 60)
    print("PART 2: DIP Applied — inject abstractions, swap freely")
    print("=" * 60)
    print()
    records = [{"id": 1, "value": "alpha"}, {"id": 2, "value": "beta"}]

    print("Configuration 1: FileLogger + SQLiteStorage")
    # Flow: PipelineRunner(FileLogger(), SQLiteStorage())
    #   → runner.run() calls self._logger.log() → FileLogger.log()
    #   → runner.run() calls self._storage.save() → SQLiteStorage.save()
    r1 = PipelineRunner(logger=FileLogger(), storage=SQLiteStorage())
    r1.run(records)

    print()
    print("Configuration 2: CloudLogger + S3Storage  (PipelineRunner unchanged)")
    r2 = PipelineRunner(logger=CloudLogger("CloudWatch"), storage=S3Storage("my-data-lake"))
    r2.run(records)

    print()
    print("Configuration 3: SilentLogger + InMemoryStorage  (testing scenario)")
    mem = InMemoryStorage()
    r3 = PipelineRunner(logger=SilentLogger(), storage=mem)
    r3.run(records)
    print(f"  InMemoryStorage captured: {mem.records}")

    print()
    print("PipelineRunner source code was never modified across all 3 configs.")


def main():
    demo_violation()
    demo_dip()


if __name__ == "__main__":
    main()

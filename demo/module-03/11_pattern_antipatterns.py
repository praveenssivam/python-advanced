"""
11_pattern_antipatterns.py
============================
Common mistakes when applying (or not applying) design patterns,
each followed by a cleaner alternative.

Anti-patterns covered:
  1. God Class — one class doing everything
  2. Unnecessary Pattern Use — Strategy for a trivial branch
  3. Inheritance Explosion — too many inheritance levels
  4. Tight Coupling via Concrete Instantiation

Run:
    python demo/module-03/11_pattern_antipatterns.py
"""

from abc import ABC, abstractmethod


# ══════════════════════════════════════════════════════════════════════════════
# ANTI-PATTERN 1: God Class
#
# Signs: 5+ distinct responsibilities, massive __init__, hard to test.
# Fix:   Split into focused collaborators (SRP — see 01_solid_single_responsibility.py).
# ══════════════════════════════════════════════════════════════════════════════

class DataHubGod:
    """BAD: one class that ingests, validates, enriches, stores, AND sends alerts."""

    def __init__(self, config: dict):
        self._config = config
        self._data: list[dict] = []
        self._errors: list[dict] = []
        self._alerts: list[str] = []

    def ingest(self, source: str) -> None:
        self._data = [{"id": 1, "val": "good"}, {"id": 2, "val": "bad"}]

    def validate(self) -> None:
        valid, invalid = [], []
        for row in self._data:
            (valid if row["val"] != "bad" else invalid).append(row)
        self._data, self._errors = valid, invalid

    def enrich(self) -> None:
        self._data = [{**row, "enriched": True} for row in self._data]

    def store(self) -> None:
        print(f"  [STORE] {len(self._data)} rows → {self._config.get('dest')}")

    def alert(self) -> None:
        if self._errors:
            print(f"  [EMAIL] Sending alert: {len(self._errors)} errors found")

    def run(self) -> None:
        self.ingest(self._config["source"])
        self.validate()
        self.enrich()
        self.store()
        self.alert()


# GOOD: each collaborator has one job (see full treatment in demo 01)

class Ingester:
    def ingest(self, source: str) -> list[dict]:
        return [{"id": 1, "val": "good"}, {"id": 2, "val": "bad"}]

class Validator:
    def validate(self, rows: list[dict]) -> tuple[list[dict], list[dict]]:
        valid = [r for r in rows if r["val"] != "bad"]
        invalid = [r for r in rows if r["val"] == "bad"]
        return valid, invalid

class Enricher:
    def enrich(self, rows: list[dict]) -> list[dict]:
        return [{**r, "enriched": True} for r in rows]

class Storer:
    def store(self, rows: list[dict], dest: str) -> None:
        print(f"  [STORE] {len(rows)} rows → {dest}")

class Alerter:
    def alert(self, errors: list[dict]) -> None:
        if errors:
            print(f"  [EMAIL] Sending alert: {len(errors)} errors found")


def demo_god_class():
    print("=" * 60)
    print("ANTI-PATTERN 1: God Class  →  Focused Collaborators")
    print("=" * 60)
    print()
    print("BAD — DataHubGod.run():")
    DataHubGod({"source": "s3://raw", "dest": "db/clean"}).run()

    print("\nGOOD — Focused collaborators:")
    rows = Ingester().ingest("s3://raw")
    clean, errors = Validator().validate(rows)
    enriched = Enricher().enrich(clean)
    Storer().store(enriched, "db/clean")
    Alerter().alert(errors)
    print("  Each class is independently testable and replaceable.")


# ══════════════════════════════════════════════════════════════════════════════
# ANTI-PATTERN 2: Pattern Overuse — Strategy for a trivial branch
#
# The Strategy pattern is valuable when algorithms are complex or
# numerous. Wrapping a single-line conditional in a class hierarchy
# adds indirection without benefit.
# ══════════════════════════════════════════════════════════════════════════════

# BAD: two Strategy classes just to toggle a flag
class CasedTransformStrategy(ABC):
    @abstractmethod
    def transform(self, value: str) -> str: ...

class UppercaseStrategy(CasedTransformStrategy):
    def transform(self, value: str) -> str:
        return value.upper()

class LowercaseStrategy(CasedTransformStrategy):
    def transform(self, value: str) -> str:
        return value.lower()

class FieldTransformerOverengineered:
    def __init__(self, strategy: CasedTransformStrategy):
        self._strategy = strategy
    def apply(self, value: str) -> str:
        return self._strategy.transform(value)


# GOOD: a simple parameter is sufficient
def transform_case(value: str, mode: str = "lower") -> str:
    """Apply case transformation. mode: 'lower' | 'upper'"""
    return value.upper() if mode == "upper" else value.lower()


def demo_overengineering():
    print("\n" + "=" * 60)
    print("ANTI-PATTERN 2: Unnecessary Pattern  →  Simple Parameter")
    print("=" * 60)
    print()

    val = "Hello_World"

    print("BAD — Strategy pattern for a two-line choice:")
    print(f"  FieldTransformerOverengineered(UppercaseStrategy()).apply(val) "
          f"= {FieldTransformerOverengineered(UppercaseStrategy()).apply(val)}")
    print("  Three classes and an ABC just to call .upper().")

    print("\nGOOD — plain function with a parameter:")
    print(f"  transform_case({val!r}, 'upper') = {transform_case(val, 'upper')}")
    print(f"  transform_case({val!r}, 'lower') = {transform_case(val, 'lower')}")
    print("  Use patterns where the complexity justifies the abstraction.")


# ══════════════════════════════════════════════════════════════════════════════
# ANTI-PATTERN 3: Inheritance Explosion
#
# Deeply nested subclass hierarchies are fragile:
#   - Method resolution order becomes hard to reason about.
#   - Each level adds coupling to all levels above it.
#   - A change in any ancestor can silently break distant leaves.
# Fix: flatten with composition or a mixin.
# ══════════════════════════════════════════════════════════════════════════════

# BAD: 4-level hierarchy
class BaseFormatterBad:
    def format(self, data: str) -> str:
        return data

class TextFormatterBad(BaseFormatterBad):
    def format(self, data: str) -> str:
        return f"[TEXT] {super().format(data)}"

class PrettyFormatterBad(TextFormatterBad):
    def format(self, data: str) -> str:
        return f"[PRETTY] {super().format(data)}"

class BoldFormatterBad(PrettyFormatterBad):
    def format(self, data: str) -> str:
        return f"[BOLD] {super().format(data)}"

class FinalFormatterBad(BoldFormatterBad):
    def format(self, data: str) -> str:
        return f"[FINAL] {super().format(data)}"


# GOOD: compose formatting steps as transformations
def apply_format_pipeline(data: str, steps: list[str]) -> str:
    """Apply named formatting steps in order. No inheritance needed."""
    _transforms = {
        "text":   lambda s: f"[TEXT] {s}",
        "pretty": lambda s: f"[PRETTY] {s}",
        "bold":   lambda s: f"[BOLD] {s}",
        "final":  lambda s: f"[FINAL] {s}",
    }
    result = data
    for step in steps:
        result = _transforms[step](result)
    return result


def demo_inheritance_explosion():
    print("\n" + "=" * 60)
    print("ANTI-PATTERN 3: Inheritance Explosion  →  Composition")
    print("=" * 60)
    print()

    data = "raw_output"

    print("BAD — 5-level inheritance chain:")
    result_bad = FinalFormatterBad().format(data)
    print(f"  {result_bad}")
    print("  5 classes, each coupled to the one above.")

    print("\nGOOD — composable transformation pipeline:")
    result_good = apply_format_pipeline(data, ["text", "pretty", "bold", "final"])
    print(f"  {result_good}")
    print("  Steps are a list — add, remove, or reorder without class changes.")


# ══════════════════════════════════════════════════════════════════════════════
# ANTI-PATTERN 4: Tight Coupling via Concrete Instantiation
#
# A class that creates its own dependencies is hard to test
# and hard to extend (covered in DIP — demo 05, repeated briefly here).
# ══════════════════════════════════════════════════════════════════════════════

# BAD: ProcessorTight creates its own storage
class HardcodedStorage:
    def save(self, rows: list[dict]) -> int:
        print(f"  [HardcodedStorage] saving {len(rows)} rows")
        return len(rows)

class ProcessorTight:
    """BAD: cannot swap storage without editing this class."""
    def __init__(self):
        self._storage = HardcodedStorage()  # ← tight coupling

    def run(self, rows: list[dict]) -> int:
        return self._storage.save(rows)


# GOOD: inject the storage
class ProcessorFlexible:
    """GOOD: accepts any object with a .save() method."""
    def __init__(self, storage):
        self._storage = storage

    def run(self, rows: list[dict]) -> int:
        return self._storage.save(rows)


def demo_tight_coupling():
    print("\n" + "=" * 60)
    print("ANTI-PATTERN 4: Tight Coupling  →  Dependency Injection")
    print("=" * 60)
    print()
    rows = [{"id": 1}, {"id": 2}]

    print("BAD — ProcessorTight owns its storage:")
    ProcessorTight().run(rows)

    print("\nGOOD — ProcessorFlexible accepts storage from outside:")
    ProcessorFlexible(HardcodedStorage()).run(rows)

    class FakeStorage:
        def save(self, rows: list[dict]) -> int:
            print(f"  [FakeStorage] captured {len(rows)} rows (no I/O)")
            return len(rows)

    ProcessorFlexible(FakeStorage()).run(rows)
    print("  FakeStorage used in tests; production code unchanged.")


def main():
    demo_god_class()
    demo_overengineering()
    demo_inheritance_explosion()
    demo_tight_coupling()


if __name__ == "__main__":
    main()

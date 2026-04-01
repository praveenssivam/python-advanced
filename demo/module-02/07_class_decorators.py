"""
07_class_decorators.py
=======================
Demonstrates class decorators:
  - A class decorator that adds metadata to a class
  - A class decorator that adds a method to a class
  - When class decorators are useful vs. when inheritance is better
  - The difference between a class decorator and a metaclass (brief note)

Run:
    python module-02/07_class_decorators.py
"""


# ══════════════════════════════════════════════════════════════════════════════
# PART 1: Class decorator that adds metadata
#
# A class decorator is just a callable that receives a CLASS and returns a CLASS.
# It follows exactly the same pattern as a function decorator:
#
#   @register_component(kind="extractor")
#   class S3Extractor: ...
#
# is equivalent to:
#   S3Extractor = register_component(kind="extractor")(S3Extractor)
#
# Flow:
#   1. register_component("extractor") is called → returns `decorator`
#   2. decorator(S3Extractor) is called → stamps cls.component_kind = "extractor"
#   3. decorator returns cls unchanged (same class object, now with extra attrs)
#   4. S3Extractor still works exactly as before — no inheritance needed.
# ══════════════════════════════════════════════════════════════════════════════

def register_component(kind: str):
    """Decorator factory: stamps a class with a component kind label.

    Returns a decorator that adds `component_kind` and `component_name`
    as class attributes. The class itself is returned unchanged — no
    wrapping, no new type, just attribute mutation.
    """

    def decorator(cls):
        # Mutate the class in-place: add two new class-level attributes.
        # The class is not replaced or wrapped — it's returned as-is, just enriched.
        cls.component_kind = kind
        cls.component_name = cls.__name__
        return cls

    return decorator


@register_component(kind="extractor")
class S3Extractor:
    """Reads data from S3."""

    def run(self, path: str) -> list:
        print(f"  Extracting from {path}")
        return [{"id": 1}, {"id": 2}]


@register_component(kind="transformer")
class DropNullsTransformer:
    """Removes rows with null values."""

    def run(self, rows: list) -> list:
        return [r for r in rows if all(v is not None for v in r.values())]


@register_component(kind="loader")
class BigQueryLoader:
    """Loads data into BigQuery."""

    def run(self, rows: list, table: str) -> None:
        print(f"  Loading {len(rows)} rows into {table}")


def demo_metadata_decorator():
    print("=" * 55)
    print("PART 1: Class decorator adding metadata")
    print("=" * 55)

    # At this point each class already has component_kind stamped on it —
    # the decorator ran at class-definition time (import time), not here.
    for cls in (S3Extractor, DropNullsTransformer, BigQueryLoader):
        print(f"{cls.__name__:30s} kind={cls.component_kind!r}")

    print()
    print("Each class carries its component_kind without inheriting from a base.")
    print("Useful when classes come from different hierarchies but share a label.")


# ══════════════════════════════════════════════════════════════════════════════
# PART 2: Class decorator that adds a method
#
# A decorator can also INJECT a new method into the class.
# Flow for @add_describe:
#   1. Python parses the class body of RunSummary.
#   2. add_describe(RunSummary) is called.
#   3. A `describe` function is defined and assigned to cls.describe.
#   4. cls (the same RunSummary object, now with describe) is returned.
#   5. RunSummary.describe exists — works like any regular instance method.
# ══════════════════════════════════════════════════════════════════════════════

def add_describe(cls):
    """Inject a describe() method into any class.

    Uses vars(self) to introspect instance attributes at call time —
    works on any class regardless of its inheritance hierarchy.
    """

    def describe(self) -> str:
        parts = [f"{cls.__name__}:"]
        for attr, val in vars(self).items():
            if not attr.startswith("_"):
                parts.append(f"  {attr} = {val!r}")
        return "\n".join(parts)

    cls.describe = describe
    return cls


@add_describe
class RunSummary:
    def __init__(self, job: str, records: int, duration_sec: float):
        self.job = job
        self.records = records
        self.duration_sec = duration_sec


def demo_add_method():
    print("\n" + "=" * 55)
    print("PART 2: Class decorator adding a method")
    print("=" * 55)

    summary = RunSummary("etl_daily", 45_000, 12.4)
    print(summary.describe())
    print()
    print("describe() was injected by the decorator — RunSummary did not inherit it.")


# ══════════════════════════════════════════════════════════════════════════════
# PART 3: Class decorator that enforces a convention
#
# Class decorators fire at CLASS-DEFINITION TIME, not at instantiation.
# This means violations are caught at import time — the earliest possible
# moment — rather than when an instance is first created.
#
# Flow for @require_docstring:
#   1. Python finishes parsing the class body.
#   2. require_docstring(cls) is called immediately.
#   3. It checks cls.__doc__ — if missing or blank, raises TypeError NOW.
#   4. The error surfaces as a module import error before any code uses the class.
# ══════════════════════════════════════════════════════════════════════════════

def require_docstring(cls):
    """Raise TypeError at class-definition time if the class has no docstring.

    Runs at import time (not instantiation). Violations are caught as early
    as possible — useful for enforcing documentation standards in large teams.
    """
    if not cls.__doc__ or not cls.__doc__.strip():
        raise TypeError(
            f"Class {cls.__name__!r} is missing a docstring. "
            f"All pipeline components must be documented."
        )
    return cls


@require_docstring
class ValidatedStep:
    """A pipeline step that has passed the documentation requirement."""

    def run(self) -> None:
        print("  Running validated step")


def demo_convention_enforcement():
    print("\n" + "=" * 55)
    print("PART 3: Class decorator enforcing a convention")
    print("=" * 55)

    step = ValidatedStep()
    step.run()

    print("\nAttempting to define a class without a docstring:")
    try:
        @require_docstring
        class UndocumentedStep:
            pass
    except TypeError as e:
        print(f"  Error at class definition: {e}")

    print()
    print("The error fired at class-definition time, not at instantiation.")
    print("This catches the problem as early as possible (during import).")


# ══════════════════════════════════════════════════════════════════════════════
# PART 4: When to use a class decorator vs. inheritance
# ══════════════════════════════════════════════════════════════════════════════

def demo_when_to_use():
    print("\n" + "=" * 55)
    print("PART 4: Class decorator vs. inheritance")
    print("=" * 55)
    print("""
  Use a class decorator when:
  ─────────────────────────────────────────────────────
  • You want to add metadata, a method, or a label
    to classes that don't share a common base.
  • You want to apply a cross-cutting concern
    (logging, registration, validation) without coupling.
  • The added behaviour is orthogonal to the class's
    domain responsibility.

  Use inheritance when:
  ─────────────────────────────────────────────────────
  • The classes share a genuine IS-A relationship.
  • Subclasses need to override behaviour, not just
    receive it.
  • You want the base class to enforce an interface
    (combine with ABC for that).

  A class decorator modifies a class from the outside.
  Inheritance builds a new type from the inside.
    """)


def main():
    demo_metadata_decorator()
    demo_add_method()
    demo_convention_enforcement()
    demo_when_to_use()


if __name__ == "__main__":
    main()

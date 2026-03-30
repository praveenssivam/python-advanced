"""
03_dataclasses_field_defaults.py
==================================
Demonstrates safe default values in dataclasses:
  - Simple scalar defaults
  - Why mutable defaults (list, dict) are forbidden as plain defaults
  - field(default_factory=...) to create a fresh container per instance
  - field(default=...) for other customisation
  - frozen=True for immutable dataclasses

Run:
    python module-02/03_dataclasses_field_defaults.py
"""

from dataclasses import dataclass, field, replace


# ══════════════════════════════════════════════════════════════════════════════
# PART 1: Scalar defaults — safe and simple
#
# Scalars (int, bool, str, float, None) are IMMUTABLE. When two instances
# both default to parallelism=4, they each hold an independent value.
# Mutating one never affects the other — there is nothing to share.
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class JobConfig:
    name: str
    parallelism: int = 4          # scalar default — safe (int is immutable)
    timeout_sec: int = 300        # scalar default — safe
    retry_on_failure: bool = True # scalar default — safe (bool is immutable)


def demo_scalar_defaults():
    print("=" * 55)
    print("PART 1: Scalar defaults")
    print("=" * 55)

    # Flow: JobConfig("ingest_job")
    #   → generated __init__ runs
    #   → name="ingest_job", parallelism=4, timeout_sec=300, retry_on_failure=True
    #   → each field gets its own independent int/bool value (immutable → safe)
    j1 = JobConfig("ingest_job")
    # Overriding specific defaults with keyword args
    j2 = JobConfig("transform_job", parallelism=8, timeout_sec=600)

    print(f"j1: {j1!r}")
    print(f"j2: {j2!r}")
    print("Scalar defaults are safe — each instance gets an independent copy.")


# ══════════════════════════════════════════════════════════════════════════════
# PART 2: Mutable default trap — why list/dict defaults are forbidden
#
# Python evaluates default argument values ONCE at definition time, not each
# time the function is called. If the default is a mutable object (list, dict),
# ALL calls that omit that argument share THE SAME OBJECT.
#
# Example trap in a regular class:
#   def __init__(self, tags=[]):   ← ONE list created at class-definition time
#       self.tags = tags           ← every instance points to that same list
#
# @dataclass detects this pattern and raises ValueError immediately:
#   "mutable default ... is not allowed: use default_factory"
# This protection is why you must use field(default_factory=list) instead.
# ══════════════════════════════════════════════════════════════════════════════

class StepBad:
    """Regular class with a mutable default — classic Python trap.

    The list `[]` is created ONCE when Python parses the class body.
    Every call to __init__ that omits `tags` receives the SAME list object.
    Appending to one instance's tags silently corrupts all other instances.
    """

    def __init__(self, name: str, tags=[]):  # <-- ONE shared list created here!
        self.name = name
        self.tags = tags  # <-- every instance that omits tags points to the same list


def demo_mutable_trap():
    print("\n" + "=" * 55)
    print("PART 2: Mutable default trap")
    print("=" * 55)

    # Both instances were created without passing tags — both got the SAME list.
    # Flow: StepBad("extract")  → __init__(self, "extract", tags=<SharedList>)
    #        self.tags = <SharedList>  ← points to the one list from class body
    s1 = StepBad("extract")
    s2 = StepBad("load")

    # Flow: s1.tags.append("critical")
    #   → mutates <SharedList>
    #   → s2.tags is also <SharedList> → s2 sees the change too!
    s1.tags.append("critical")
    print(f"s1.tags after append: {s1.tags}")
    print(f"s2.tags — untouched? : {s2.tags}")
    print("Both share the same list! Mutation through s1 is visible in s2.")
    print()

    # @dataclass catches this at class-definition time — before any instance is
    # created — and raises ValueError. The protection fires during the exec() call
    # below, which simulates what Python does when parsing a @dataclass body.
    print("Attempting: @dataclass with tags: list = []  ...")
    try:
        # Evaluated at definition time — raises ValueError
        exec(
            "from dataclasses import dataclass\n"
            "@dataclass\n"
            "class BadDC:\n"
            "    tags: list = []\n"
        )
    except ValueError as e:
        print(f"  dataclass raises ValueError: {e}")
    print("dataclass protects you by refusing mutable defaults.")


# ══════════════════════════════════════════════════════════════════════════════
# PART 3: field(default_factory=...) — the correct pattern
#
# field(default_factory=list) tells @dataclass:
#   "when creating a new instance, CALL list() to produce a fresh empty list".
# The factory is called once PER INSTANCE — no sharing.
#
# Rule of thumb:
#   Immutable default (int, str, bool, None)  → use a plain  = value
#   Mutable default  (list, dict, set)        → use  field(default_factory=...)
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class PipelineStep:
    """A single step in a pipeline. All collection fields use default_factory.

    Each instance gets its own independent list and dict objects —
    no cross-instance sharing is possible.
    """
    name: str
    # default_factory=list creates a NEW list for each instance
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)


def demo_default_factory():
    print("\n" + "=" * 55)
    print("PART 3: field(default_factory=...) — safe mutable defaults")
    print("=" * 55)

    # Flow: PipelineStep("extract")
    #   → generated __init__ calls list() → new list A for step1.tags
    #   → generated __init__ calls list() → new list B for step1.depends_on
    #   → generated __init__ calls dict() → new dict C for step1.metadata
    step1 = PipelineStep("extract")
    # Flow: PipelineStep("transform")
    #   → list() called again → new list D (different object from A!) for step2.tags
    step2 = PipelineStep("transform")

    # Mutating step1's list only affects step1 — step2 has list D, not list A
    step1.tags.append("critical")
    step1.metadata["owner"] = "team-data"

    print(f"step1.tags     : {step1.tags}")
    print(f"step2.tags     : {step2.tags}")   # still empty — independent list
    print(f"step1.metadata : {step1.metadata}")
    print(f"step2.metadata : {step2.metadata}")  # still empty
    print("step1 and step2 have independent lists and dicts.")
    print()

    # Passing explicit values at construction overrides the factory entirely
    step3 = PipelineStep("load", tags=["nightly", "s3"], depends_on=["transform"])
    print(f"step3: {step3!r}")


# ══════════════════════════════════════════════════════════════════════════════
# PART 4: field() for other customisation
#
# field() lets you control additional aspects of each field beyond its default:
#
#   repr=False   — exclude this field from the generated __repr__.
#                  Useful for large binary blobs, secrets, or internal state
#                  that would clutter the debug output.
#
#   init=False   — exclude this field from __init__ entirely. The generated
#                  __init__ will NOT accept it as an argument. The field must be
#                  set inside __post_init__ or by a method (e.g., commit()).
#                  Signals: "this is computed state, not constructor input".
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Checkpoint:
    run_id: str
    records_written: int
    # repr=False — excluded from repr (e.g. large or sensitive fields)
    raw_payload: bytes = field(default=b"", repr=False)
    # init=False — not a constructor argument; set after construction via commit()
    is_committed: bool = field(default=False, init=False)

    def commit(self) -> None:
        self.is_committed = True


def demo_field_options():
    print("\n" + "=" * 55)
    print("PART 4: field() for repr and init control")
    print("=" * 55)

    # Flow: Checkpoint("run-007", 45_000, raw_payload=b"\x00" * 1024)
    #   → generated __init__ accepts run_id, records_written, raw_payload
    #   → is_committed is NOT in __init__ (init=False) → must not be passed
    #   → is_committed is initialised to False by the generated __init__ body
    cp = Checkpoint("run-007", 45_000, raw_payload=b"\x00" * 1024)

    # Flow: repr(cp)
    #   → generated __repr__ formats run_id, records_written, is_committed
    #   → raw_payload is SKIPPED (repr=False) → won't appear in logs
    print(f"Before commit: {cp!r}")
    print("  raw_payload is excluded from repr (repr=False).")
    print("  is_committed is not in __init__ (init=False).")

    # commit() is a hand-written method that promotes is_committed to True
    cp.commit()
    print(f"After commit:  {cp!r}")


# ══════════════════════════════════════════════════════════════════════════════
# PART 5: frozen=True — immutable dataclass
#
# frozen=True has two effects:
#   1. All field assignments after construction raise FrozenInstanceError.
#      The generated __setattr__ and __delattr__ both raise it.
#   2. __hash__ IS generated (based on all fields). Without frozen=True,
#      @dataclass sets __hash__ = None when __eq__ is defined, making
#      the class unhashable. With frozen=True, instances can be used
#      in sets and as dictionary keys.
#
# To "change" a frozen instance, use dataclasses.replace() (see PART 6).
# ══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class SchemaVersion:
    """Immutable — once created, fields cannot be changed.

    frozen=True also generates __hash__, making instances usable in sets
    and as dictionary keys.
    """
    name: str
    version: int
    format: str


def demo_frozen():
    print("\n" + "=" * 55)
    print("PART 5: frozen=True — immutable dataclass")
    print("=" * 55)

    v1 = SchemaVersion("events", 3, "json")
    print(f"v1: {v1!r}")

    try:
        v1.version = 4  # type: ignore
    except Exception as e:
        print(f"Cannot mutate frozen dataclass: {type(e).__name__}: {e}")

    # frozen + __hash__ → usable as dict key or set member
    schema_registry = {v1: "https://schema.example.com/events/v3"}
    print(f"Used as dict key: {schema_registry[v1]}")

    v2 = SchemaVersion("events", 3, "json")
    print(f"v1 == v2: {v1 == v2}")      # True — same field values
    print(f"v1 in {{v1}}: {v1 in {v1}}")  # True — hashable


# ══════════════════════════════════════════════════════════════════════════════
# PART 6: dataclasses.replace() — create a modified copy
# ══════════════════════════════════════════════════════════════════════════════
#
# replace(instance, **changes) returns a NEW instance with only the specified
# fields swapped. The original is untouched.
# Think of it as "copy with overrides" — essential for frozen dataclasses
# (which cannot be mutated) and useful anywhere you want immutable-style updates.

@dataclass
class JobConfig:
    name: str
    parallelism: int = 4
    timeout_sec: int = 300
    retry_on_failure: bool = True


def demo_replace():
    print("\n" + "=" * 55)
    print("PART 6: dataclasses.replace() — copy with overrides")
    print("=" * 55)

    base = JobConfig("etl_daily")
    print(f"original : {base!r}")

    # Create a new config with only parallelism changed
    scaled_up = replace(base, parallelism=16)
    print(f"scaled   : {scaled_up!r}")
    print(f"original unchanged: {base!r}")
    print()

    # Fine-grained override — change multiple fields at once
    retry_cfg = replace(base, timeout_sec=600, retry_on_failure=False)
    print(f"retry_cfg: {retry_cfg!r}")
    print()

    # Replace is especially useful with frozen dataclasses
    # (the only way to "change" a field on a frozen instance)
    v1 = SchemaVersion("events", 3, "json")
    v2 = replace(v1, version=4)
    print(f"v1 (original): {v1!r}")
    print(f"v2 (replaced): {v2!r}")
    print("v1 is unchanged — replace() always produces a new object.")
    print()

    # Common pattern: apply a list of overrides to produce variants
    overrides = [
        {"parallelism": 2},
        {"parallelism": 8, "timeout_sec": 120},
        {"retry_on_failure": False},
    ]
    variants = [replace(base, **ov) for ov in overrides]
    print("Variants derived from base config:")
    for v in variants:
        print(f"  {v!r}")


def main():
    demo_scalar_defaults()
    demo_mutable_trap()
    demo_default_factory()
    demo_field_options()
    demo_frozen()
    demo_replace()


if __name__ == "__main__":
    main()

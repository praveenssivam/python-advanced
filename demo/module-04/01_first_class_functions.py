"""
01_first_class_functions.py
=============================
Functions are first-class objects in Python:
  - They can be assigned to variables.
  - They can be passed as arguments to other functions.
  - They can be stored in data structures and iterated.
  - They can be returned from functions.

This is the foundation of functional programming in Python.

Run:
    python demo/module-04/01_first_class_functions.py
"""


# ══════════════════════════════════════════════════════════════════════════════
# PART 1: Functions are objects — assign, inspect, compare
#
# When Python evaluates  def my_func(): ...
# it creates a function object and binds the name 'my_func' to it.
#
# Reassigning the name is just rebinding — the function object still exists.
# The function object has its own attributes: __name__, __doc__, etc.
# ══════════════════════════════════════════════════════════════════════════════

def greet(name: str) -> str:
    """Return a greeting string."""
    return f"Hello, {name}!"


def shout(name: str) -> str:
    """Return an uppercased greeting."""
    return f"HELLO, {name.upper()}!"


def demo_functions_as_objects():
    print("=" * 55)
    print("PART 1: Functions are objects")
    print("=" * 55)
    print()

    # Flow: 'greet' is just a name bound to a function object
    #   fn = greet → fn now refers to the SAME function object
    #   fn("Alice") → calls greet("Alice")
    fn = greet
    print(f"greet is fn:       {greet is fn}")       # same object
    print(f"fn('Alice'):        {fn('Alice')}")
    print(f"fn.__name__:        {fn.__name__}")       # function object attribute
    print(f"fn.__doc__:         {fn.__doc__!r}")

    print()
    # Functions can live in a list and be iterated
    # Flow: [greet, shout] → iterate → call each with "Bob"
    transforms = [greet, shout]
    print("Functions in a list:")
    for t in transforms:
        print(f"  {t.__name__}('Bob') → {t('Bob')}")


# ══════════════════════════════════════════════════════════════════════════════
# PART 2: Functions as arguments — higher-order functions
#
# A higher-order function accepts or returns another function.
# This enables generic operations:
#   apply_to_each(fn, items) — call fn on every item
#   apply_many(fns, value)   — run a list of functions on one value in order
#
# Python's built-in map() and filter() are the archetypal examples.
# ══════════════════════════════════════════════════════════════════════════════

def apply_to_each(transform_fn, items: list) -> list:
    """Apply transform_fn to every item; return new list.

    Flow: apply_to_each(fn, [a, b, c])
      → [fn(a), fn(b), fn(c)]
    """
    return [transform_fn(item) for item in items]


def apply_many(fns: list, value: str) -> str:
    """Apply each function in fns to value in sequence.

    Flow: apply_many([f1, f2, f3], value)
      → f3(f2(f1(value)))
    (Left-to-right pipeline: each output becomes the next input.)
    """
    result = value
    for fn in fns:
        result = fn(result)
    return result


def demo_higher_order():
    print("\n" + "=" * 55)
    print("PART 2: Higher-order functions")
    print("=" * 55)
    print()

    # Flow: apply_to_each(str.upper, ["alice", "bob"])
    #   → [str.upper("alice"), str.upper("bob")]
    #   → ["ALICE", "BOB"]
    names = ["alice", "bob", "carol"]
    print("apply_to_each(str.upper, names):")
    print(f"  {apply_to_each(str.upper, names)}")

    # Flow: apply_to_each(len, words) → [len(w) for w in words]
    words = ["python", "is", "expressive"]
    print(f"\napply_to_each(len, {words}):")
    print(f"  {apply_to_each(len, words)}")

    print()
    # Pipeline of three string transforms applied in order
    # Flow: apply_many([strip, lower, title], "  hello world  ")
    #   → strip("  hello world  ") → "hello world"
    #   → lower("hello world")     → "hello world"
    #   → title("hello world")     → "Hello World"
    pipeline = [str.strip, str.lower, str.title]
    messy = "  HELLO WORLD  "
    print(f"apply_many([strip, lower, title], {messy!r}):")
    print(f"  → {apply_many(pipeline, messy)!r}")


# ══════════════════════════════════════════════════════════════════════════════
# PART 3: Functions returned from functions — factories
#
# A function that builds and returns another function is a factory.
# The returned function closes over variables from the outer scope.
#
# Flow for make_prefix_adder("col_"):
#   1. Python enters make_prefix_adder("col_")
#   2. Defines inner add_prefix(name) capturing prefix="col_"
#   3. Returns add_prefix (the function object)
#   4. Caller receives a callable that "remembers" prefix
# ══════════════════════════════════════════════════════════════════════════════

def make_prefix_adder(prefix: str):
    """Return a function that prepends prefix to any string."""
    def add_prefix(name: str) -> str:
        return f"{prefix}{name}"
    return add_prefix  # return the function object, not the result


def make_validator(min_length: int, max_length: int):
    """Return a function that validates string length."""
    def validate(value: str) -> bool:
        return min_length <= len(value) <= max_length
    return validate


def demo_function_factories():
    print("\n" + "=" * 55)
    print("PART 3: Functions returned from functions")
    print("=" * 55)
    print()

    # Flow: make_prefix_adder("col_")
    #   → creates add_prefix capturing prefix="col_"
    #   → returns add_prefix
    col_prefix = make_prefix_adder("col_")
    metric_prefix = make_prefix_adder("metric_")

    print("make_prefix_adder('col_'):")
    print(f"  col_prefix('distance')  = {col_prefix('distance')!r}")
    print(f"  col_prefix('duration')  = {col_prefix('duration')!r}")

    print()
    print("make_prefix_adder('metric_'):  (different closure, independent)")
    print(f"  metric_prefix('latency')    = {metric_prefix('latency')!r}")

    print()
    # Flow: make_validator(3, 20) → returns validate(value)
    #   → validate("alice") → 3 <= 5 <= 20 → True
    is_valid_username = make_validator(min_length=3, max_length=20)
    is_valid_code = make_validator(min_length=6, max_length=6)

    print("make_validator(3, 20) for usernames:")
    for v in ["ab", "alice", "a" * 25]:
        print(f"  is_valid_username({v!r}) = {is_valid_username(v)}")

    print()
    print("make_validator(6, 6) for fixed-length codes:")
    for v in ["abc", "ABC123", "ABCDEFG"]:
        print(f"  is_valid_code({v!r}) = {is_valid_code(v)}")


# ══════════════════════════════════════════════════════════════════════════════
# PART 4: Functions in data structures — dispatch tables
#
# Storing functions in a dict enables a clean alternative to if/elif chains.
# This is the foundation of the registry-based Factory pattern (Module 3, demo 07).
# ══════════════════════════════════════════════════════════════════════════════

def clean_upper(s: str) -> str:
    return s.strip().upper()

def clean_lower(s: str) -> str:
    return s.strip().lower()

def clean_title(s: str) -> str:
    return s.strip().title()

def clean_strip(s: str) -> str:
    return s.strip()


TRANSFORM_TABLE = {
    "upper":  clean_upper,
    "lower":  clean_lower,
    "title":  clean_title,
    "strip":  clean_strip,
}


def apply_transform(value: str, transform_name: str) -> str:
    """Apply a named transform from the dispatch table.

    Flow: look up transform_name in TRANSFORM_TABLE → call fn(value)
    No if/elif needed; adding 'slug' means TRANSFORM_TABLE["slug"] = fn.
    """
    if transform_name not in TRANSFORM_TABLE:
        raise ValueError(f"Unknown transform {transform_name!r}. Known: {list(TRANSFORM_TABLE)}")
    return TRANSFORM_TABLE[transform_name](value)


def demo_dispatch_table():
    print("\n" + "=" * 55)
    print("PART 4: Functions in a dispatch table")
    print("=" * 55)
    print()

    value = "  hello world  "
    for name in ["strip", "upper", "lower", "title"]:
        # Flow: TRANSFORM_TABLE["upper"] → clean_upper → returns value.strip().upper()
        result = apply_transform(value, name)
        print(f"  apply_transform({value!r}, {name!r}) → {result!r}")

    print()
    try:
        apply_transform(value, "slug")
    except ValueError as e:
        print(f"  Unknown transform: {e}")


def main():
    demo_functions_as_objects()
    demo_higher_order()
    demo_function_factories()
    demo_dispatch_table()


if __name__ == "__main__":
    main()

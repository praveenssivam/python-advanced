"""
01_references_and_mutability.py
================================
Demonstrates how Python names work as references to objects,
what aliasing means, how mutation through one name is visible
through another, and how reassignment differs from mutation.

Run:
    python module-01/01_references_and_mutability.py
"""


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1: Names are references, not containers
#
# A Python variable is a NAME that POINTS TO an object in memory.
# The object lives on the heap; the name is just a label attached to it.
# Multiple names can point to the same object at the same time.
#
# Flow for  x = 42; y = x; x = 100:
#   1. x = 42   → name 'x' bound to int object 42  (id: A)
#   2. y = x    → name 'y' also bound to int object 42  (id: A)  x is y → True
#   3. x = 100  → name 'x' rebound to a NEW int object 100  (id: B)
#                 name 'y' STILL points at int 42  (id: A)  — unaffected
# ══════════════════════════════════════════════════════════════════════════════

def demo_names_and_references():
    print("=" * 50)
    print("SECTION 1: Names are references, not containers")
    print("=" * 50)

    x = 42          # Flow: 'x' → int object 42
    y = x           # Flow: 'y' → same int object 42  (x is y → True)

    print(f"x = {x}, y = {y}")
    print(f"Same object? {x is y}")  # True — both point to int 42

    # Reassign x — creates a NEW int object (100) and rebinds the name 'x'.
    # 'y' is unaffected; it still labels the original 42 object.
    x = 100         # Flow: 'x' → new int object 100; 'y' stays → 42
    print(f"\nAfter x = 100:")
    print(f"x = {x}, y = {y}")
    print(f"y is unchanged — reassignment rebinds x to a new object, y still points to 42")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2: Aliasing — two names, one mutable object
#
# When you write  pipeline_b = pipeline_a  you are NOT copying the list.
# Both names now point to THE SAME list object on the heap.
# Mutating the list through either name is visible through the other.
#
# Flow for  pipeline_b = pipeline_a; pipeline_b.append("load"):
#   1. pipeline_a → list ["extract", "transform"]  (id: X)
#   2. pipeline_b = pipeline_a → pipeline_b → same list  (id: X)
#   3. pipeline_b.append("load") → mutates list at id: X
#   4. pipeline_a now also shows ["extract", "transform", "load"]
#      because pipeline_a still points to id: X
# ══════════════════════════════════════════════════════════════════════════════

def demo_aliasing_mutable():
    print("\n" + "=" * 50)
    print("SECTION 2: Aliasing — two names, one mutable object")
    print("=" * 50)

    pipeline_a = ["extract", "transform"]
    pipeline_b = pipeline_a  # Both names point to the same list

    print(f"pipeline_a: {pipeline_a}")
    print(f"pipeline_b: {pipeline_b}")
    print(f"Same object? {pipeline_a is pipeline_b}")

    # Mutate through pipeline_b
    pipeline_b.append("load")

    print(f"\nAfter pipeline_b.append('load'):")
    print(f"pipeline_a: {pipeline_a}")  # Also changed!
    print(f"pipeline_b: {pipeline_b}")
    print("Both names reflect the change — they share the same list object.")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3: Breaking aliasing with a copy
#
# list.copy() (or list[:] or list(original)) creates a SHALLOW COPY:
# a brand-new list object whose elements are the same objects as the original.
# The two lists are now independent — mutating one does not affect the other.
#
# Flow for  independent = original.copy(); independent.append("step3"):
#   1. original     → list ["step1", "step2"]  (id: A)
#   2. independent  = original.copy() → NEW list ["step1", "step2"]  (id: B)
#   3. independent.append("step3") → mutates id: B only
#   4. original (id: A) is unchanged
# ══════════════════════════════════════════════════════════════════════════════

def demo_copy_to_break_aliasing():
    print("\n" + "=" * 50)
    print("SECTION 3: Breaking aliasing with a copy")
    print("=" * 50)

    original = ["step1", "step2"]
    independent = original.copy()  # A new list with the same contents

    independent.append("step3")

    print(f"original:    {original}")
    print(f"independent: {independent}")
    print("original is unaffected — independent has its own list object.")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4: Immutable objects — reassignment creates a new object
#
# Strings, ints, floats, and tuples are IMMUTABLE: once created, their value
# cannot change.  You can only rebind the name to a different object.
#
# Flow for  status = "pending"; status = "complete":
#   1. status = "pending"  → name 'status' bound to str object "pending" (id: A)
#   2. status = "complete" → name 'status' rebound to a NEW str object "complete" (id: B)
#                             The original "pending" object (id: A) is unchanged
#                             (and will be garbage-collected when no name references it)
#
# Flow for  count += 1  (where count = 0):
#   1. count = 0         → name 'count' → int object 0  (id: C)
#   2. count += 1        → Python evaluates count + 1 → new int object 1  (id: D)
#                           then rebinds 'count' to id: D
# ══════════════════════════════════════════════════════════════════════════════

def demo_immutable_reassignment():
    print("\n" + "=" * 50)
    print("SECTION 4: Immutable objects — reassignment creates a new object")
    print("=" * 50)

    status = "pending"               # Flow: 'status' → str "pending" (id A)
    print(f"status = '{status}', id = {id(status)}")

    status = "complete"              # Flow: 'status' → NEW str "complete" (id B)
    print(f"status = '{status}', id = {id(status)}")
    print("Strings are immutable — 'status = ...' always creates a new string object.")

    print()
    count = 0
    original_id = id(count)
    count += 1
    print(f"count after += 1: {count}, same object? {id(count) == original_id}")
    print("Integers are immutable too — += creates a new int object and rebinds the name.")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5: Mutable default argument — a common mistake
#
# Python evaluates default argument values ONCE when the function is DEFINED,
# not each time it is called.  If the default is a mutable object (list, dict),
# all calls without that argument share the SAME object.
#
# Flow for  add_item_bad("alpha"); add_item_bad("beta"):
#   1. def add_item_bad(item, collection=[]):
#        → default list [] created once at function definition  (id: X)
#   2. add_item_bad("alpha")  → collection is id: X; appends "alpha" → ["alpha"]
#   3. add_item_bad("beta")   → collection is STILL id: X; appends "beta"
#        → ["alpha", "beta"]  — the same list both calls share!
#
# Fix: use None as the sentinel, create a fresh list inside the function.
# ══════════════════════════════════════════════════════════════════════════════

def demo_mutable_default_warning():
    print("\n" + "=" * 50)
    print("SECTION 5: Mutable default argument — a common mistake")
    print("=" * 50)

    # BAD: the default list is created once and shared across all calls
    def add_item_bad(item, collection=[]):
        collection.append(item)
        return collection

    r1 = add_item_bad("alpha")
    r2 = add_item_bad("beta")
    print(f"BAD — call 1 result: {r1}")
    print(f"BAD — call 2 result: {r2}")
    print("Both calls share the same list — this is almost never what you want.")

    # GOOD: use None as sentinel, create a fresh list each call
    def add_item_good(item, collection=None):
        if collection is None:
            collection = []
        collection.append(item)
        return collection

    r3 = add_item_good("alpha")
    r4 = add_item_good("beta")
    print(f"\nGOOD — call 1 result: {r3}")
    print(f"GOOD — call 2 result: {r4}")
    print("Each call gets its own list.")


def main():
    demo_names_and_references()
    demo_aliasing_mutable()
    demo_copy_to_break_aliasing()
    demo_immutable_reassignment()
    demo_mutable_default_warning()


if __name__ == "__main__":
    main()

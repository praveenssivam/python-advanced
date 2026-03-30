# Module 2 — Module 2: Advanced Object Modeling

## Learning Goals

By the end of Module 2, you will be able to:

- Explain Python's data model and how dunder methods hook into built-in behaviour
- Implement `__repr__` and `__eq__` to make objects readable and comparable
- Use `@dataclass` to eliminate boilerplate and express data-centric types clearly
- Use `field(default_factory=...)` to handle mutable defaults correctly
- Build properties for computed values, validation, and controlled access
- Write class- and function-based context managers for deterministic resource cleanup
- Write function decorators with `functools.wraps` to preserve metadata
- Write class decorators that add behaviour or metadata without inheritance
- Use `__init_subclass__` to build a self-registering plugin system
- Combine all of the above into a coherent, compact design

---

## Demo File Order

| File | Topic |
|------|-------|
| `01_repr_and_eq.py` | `__repr__`, `__str__`, `__eq__` |
| `02_dataclasses_basics.py` | `@dataclass` vs regular class |
| `03_dataclasses_field_defaults.py` | `field()`, `default_factory`, `frozen=True` |
| `04_properties_advanced.py` | Computed property, validation setter, stored vs presented value |
| `05_context_managers.py` | Class-based and function-based context managers |
| `06_function_decorators.py` | Wrapping, `functools.wraps`, stacking |
| `07_class_decorators.py` | Class decorators for metadata and behaviour |
| `08_init_subclass_registry.py` | Plugin auto-registration with `__init_subclass__` |
| `09_combined_modeling_demo.py` | All techniques in one cohesive example |

---

## How to Run

From the **repository root** with `.venv` activated:

```bash
python module-02/01_repr_and_eq.py
python module-02/02_dataclasses_basics.py
python module-02/03_dataclasses_field_defaults.py
python module-02/04_properties_advanced.py
python module-02/05_context_managers.py
python module-02/06_function_decorators.py
python module-02/07_class_decorators.py
python module-02/08_init_subclass_registry.py
python module-02/09_combined_modeling_demo.py
```

---

## What to Observe in Output

- **01**: Without `__repr__`, `print(obj)` shows `<ClassName object at 0x...>`. After adding it, output is human-readable. `__eq__` based on state means two objects with the same fields compare as equal.
- **02**: The dataclass version is shorter but generates the same `__init__`, `__repr__`, and `__eq__` that you would otherwise write by hand.
- **03**: The mutable default trap — a list default on a regular class shares the list across all instances. `field(default_factory=list)` creates a fresh list per instance every time.
- **04**: The computed property recalculates from stored state. The setter validates before storing. The property separates the user-facing value from the internal representation.
- **05**: `__exit__` is called even when an exception is raised inside the `with` block. The `@contextmanager` generator style is more compact for simple cases.
- **06**: A decorator wraps the function. Without `functools.wraps`, `__name__` and `__doc__` are lost. Stacked decorators apply from the inside out.
- **07**: A class decorator modifies or annotates the class without using inheritance. Useful for auto-registration, adding meta-attributes, or enforcing naming conventions.
- **08**: Subclasses register themselves automatically just by existing — the base class does not need to know about them in advance.
- **09**: Watch how each technique plays a specific role. No single technique dominates — they compose cleanly.

---

## Suggested Trainer Flow

1. **01**: Open the REPL, create a plain object, show the ugly default repr. Then add `__repr__`. Compare `==` before and after `__eq__`.
2. **02**: Show a regular class, count the lines. Then show the dataclass — same behaviour, fewer lines. Ask: "What would happen if we forgot `__eq__`?"
3. **03**: Live-demo the mutable default trap — create two instances, append to one, show the other is affected. Then fix it with `field(default_factory=list)`.
4. **04**: Mutate the stored value and show the computed property updating automatically. Try setting an invalid value — show the rejection.
5. **05**: Ask attendees: "What if the `with` block raises — does cleanup still happen?" Run the error case live.
6. **06**: Build the decorator live from scratch, show the name/doc loss, fix with `functools.wraps`.
7. **07**: Show a class without the decorator, then apply it. Ask: "When would inheritance be better here?"
8. **08**: Add a new plugin subclass live — show the registry update without touching the base class.
9. **09**: Walk through the combined demo top to bottom. Identify each technique as it appears.

---

## Optional Extension Ideas

- **01**: Add `__hash__` and use objects as dictionary keys or in sets.
- **02**: Add `order=True` to `@dataclass` and sort a list of instances.
- **03**: Add `__post_init__` to a dataclass for post-construction validation.
- **04**: Chain two properties (e.g., `Celsius` property derives `Kelvin` from `Fahrenheit`).
- **05**: Write a context manager that measures and prints the wall-clock time of a block.
- **06**: Write a decorator that caches the result of a function (manual `lru_cache`).
- **07**: Write a class decorator that enforces that every method has a docstring.
- **08**: Add a `version` field to each plugin and make the registry store it.
- **09**: Add a second plugin type to the combined demo and observe the registry handling both.

# Module 1 — Python Foundations Bridge + Module 1: OOP Refresher & Code Design

## Learning Goals

By the end of Module 1, you will be able to:

- Explain how Python names and references work, and why mutability matters
- Write functions with clear parameters, return values, and scoped state
- Use exceptions correctly: raising, catching, and cleaning up
- Organise code across modules and control what gets imported
- Define classes with proper instance and class state separation
- Apply encapsulation and properties to protect and validate data
- Choose between inheritance and composition with confidence
- Use Abstract Base Classes to define contracts
- Recognise and fix common OOP anti-patterns

---

## Demo File Order

| File | Topic |
|------|-------|
| `01_references_and_mutability.py` | Names, references, aliasing, mutable vs immutable |
| `02_functions_and_exceptions.py` | Parameters, returns, scope, exceptions |
| `03_modules_demo/main.py` | Modules and imports |
| `04_class_vs_instance.py` | Class attributes vs instance attributes |
| `05_encapsulation_and_properties.py` | Encapsulation, `@property`, validation |
| `06_inheritance_vs_composition.py` | Inheritance model vs composition model |
| `07_method_overriding_and_abc.py` | `super()`, ABCs, `@abstractmethod` |
| `08_oop_antipatterns.py` | God object, tight coupling, inheritance misuse |

---

## How to Run

From the **repository root** with `.venv` activated:

```bash
python module-01/01_references_and_mutability.py
python module-01/02_functions_and_exceptions.py
python module-01/03_modules_demo/main.py
python module-01/04_class_vs_instance.py
python module-01/05_encapsulation_and_properties.py
python module-01/06_inheritance_vs_composition.py
python module-01/07_method_overriding_and_abc.py
python module-01/08_oop_antipatterns.py
```

---

## What to Observe in Output

- **01**: Notice how two names can point to the same list — mutation through one is visible through the other. Also see that rebinding an integer name does not affect the other name.
- **02**: Observe the controlled flow through `try/except/else/finally` — `else` runs only on success, `finally` always runs.
- **03**: Notice the clean import examples. `helpers.py` does not execute on import because of the `__name__` guard.
- **04**: See that class attributes are shared, while instance attributes are independent.
- **05**: A property setter validates and rejects invalid values without exposing internal state.
- **06**: Composition gives the `ReportService` the ability to swap formatters without changing the class itself.
- **07**: Attempting to instantiate an abstract class raises `TypeError` immediately.
- **08**: The God object tries to do everything; the refactored version splits responsibilities clearly.

---

## Suggested Trainer Flow

1. Start with `01` — draw a diagram on the board showing names pointing to objects.
2. For `02`, ask: "What happens if the `finally` block also raises an exception?"
3. For `03`, open both files side-by-side to show the import relationship visually.
4. For `04-05`, live-edit the class to add a second instance and mutate a class attribute.
5. For `06`, explicitly ask: "If `HTMLFormatter` gains a new method, does `ReportService` need to change?"
6. For `07`, try to instantiate `Exporter` directly in the REPL to show the TypeError.
7. For `08`, present the bad version first — ask attendees to identify the problems before revealing the fix.

---

## Optional Extension Ideas

- In `01`: What happens when you mutate a nested list inside a tuple?
- In `02`: Write a decorator that handles exceptions uniformly (preview of Module 2).
- In `04`: Add a `__del__` method and observe when it fires.
- In `06`: Add a third formatter (e.g., `MarkdownFormatter`) to the composition example without changing `ReportService`.
- In `07`: Add a second abstract method and observe what happens when a subclass implements only one.
- In `08`: Try converting the God object into a set of small collaborating classes.

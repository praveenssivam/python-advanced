# Module 3: Design Patterns

## Learning Goals

- Apply the five SOLID principles to diagnose and fix real design problems
- Implement the Strategy, Factory, and Observer patterns from scratch
- Choose between ABC and Protocol for interface design
- Recognise and fix common anti-patterns before they accumulate in a codebase

---

## Topics Covered

| File | Concept | Key Idea |
|---|---|---|
| `01_solid_single_responsibility.py` | SRP | One class → one reason to change |
| `02_solid_open_closed.py` | OCP | Open for extension, closed for modification |
| `03_solid_liskov_substitution.py` | LSP | Subclass must not break parent's contract |
| `04_solid_interface_segregation.py` | ISP | Small interfaces, no forced stubs |
| `05_solid_dependency_inversion.py` | DIP | Depend on abstractions, inject implementations |
| `06_strategy_pattern.py` | Strategy | Select algorithm at runtime |
| `07_factory_pattern.py` | Factory | Create objects by name from config |
| `08_observer_pattern.py` | Observer | Notify interested parties without coupling |
| `09_interface_design.py` | ABC vs Protocol | Explicit contract vs structural typing |
| `10_extensible_design_combined.py` | Combined | Strategy + Factory + Observer together |
| `11_pattern_antipatterns.py` | Anti-patterns | God class, overuse, explosion, coupling |

---

## SOLID Principles at a Glance

| Letter | Principle | One-line rule |
|---|---|---|
| **S** | Single Responsibility | A class has one reason to change |
| **O** | Open/Closed | Add new behaviour by adding code, not changing it |
| **L** | Liskov Substitution | Subclass is safely usable wherever parent is used |
| **I** | Interface Segregation | Don't force clients to depend on methods they don't use |
| **D** | Dependency Inversion | Depend on abstractions; inject concretions from outside |

---

## Patterns at a Glance

### Strategy
Define a family of algorithms, encapsulate each, make them interchangeable.
```
Context → Strategy interface → ConcreteStrategyA / B / C
                                            ↕ selected at runtime
```

### Factory (Registry)
Centralise object creation. Callers ask for objects by type name.
```
Factory._registry = {"csv": CSVConnector, "json": JSONConnector}
Factory.create({"type": "csv", "path": ...}) → CSVConnector(...)
```

### Observer
Subject maintains a list of observers. Notifies all when state changes.
```
Subject.notify(event) → [obs1.handle(event), obs2.handle(event), ...]
Adding a new observer: subject.attach(new_obs) — subject never changes
```

---

## How to Run

### Prerequisites
- Python 3.10+
- Virtual environment activated: `source .venv/bin/activate`

### Running Demos

```bash
# From the repository root
python demo/module-03/01_solid_single_responsibility.py
python demo/module-03/02_solid_open_closed.py
python demo/module-03/03_solid_liskov_substitution.py
python demo/module-03/04_solid_interface_segregation.py
python demo/module-03/05_solid_dependency_inversion.py
python demo/module-03/06_strategy_pattern.py
python demo/module-03/07_factory_pattern.py
python demo/module-03/08_observer_pattern.py
python demo/module-03/09_interface_design.py
python demo/module-03/10_extensible_design_combined.py
python demo/module-03/11_pattern_antipatterns.py
```

---

## What to Observe

- **01_SRP**: "BAD" output shows one class doing everything. "GOOD" output shows clean delegation — each collaborator logs one action.
- **02_OCP**: Adding `StartsWithRule` produces output without touching the existing if/elif function. The final print confirms no existing code was modified.
- **03_LSP**: The violation section shows `NotImplementedError` crashing the pipeline mid-loop. The fixed section shows all four exporters processing the same data list without a single branch or error.
- **04_ISP**: `S3ReadConnector` is created and used — it never mentions `write_records`. The absence of a `NotImplementedError` stub is the point.
- **05_DIP**: Three different `(logger, storage)` combinations produce identical pipeline behaviour with different output lines — `PipelineRunner` source never changed.
- **06_Strategy**: Watch `v.strategy = RegexStrategy(...)` swap the algorithm mid-demo. Same validator object; different behaviour.
- **07_Factory**: `ConnectorFactory.create({"type": "xml", ...})` succeeds after one `register()` call — no if/elif was edited.
- **08_Observer**: `AlertObserver` fires only on the second pipeline. The `PipelineRunner` code is identical in both runs.
- **09_Interface**: `TSVFormatter` satisfies `FormatterProtocol` via structural match but `isinstance(tsv, ABCFormatter)` returns `False`.
- **10_Combined**: The `ValidationEngine` output shows rules + listeners cooperating. Adding `AllowlistRule` and `StrictListener` to a second engine requires no engine edits.
- **11_Anti-patterns**: Each "BAD" section highlights the inflexibility; the "GOOD" section shows the minimal fix.

---

## Suggested Trainer Flow

1. **SOLID (30 min)**: Walk through 01–05 in order. For each: *show the bad*, ask students *what breaks*, then show the fix. Emphasise that the principles encode the same insights from different angles.
2. **Patterns (30 min)**: 06 (Strategy) → 07 (Factory) → 08 (Observer). Each extends the previous: the combined demo ties them together.
3. **Interfaces (15 min)**: Run 09 side-by-side. Ask: "If this formatter came from a third-party library you don't control, which interface works?"
4. **Anti-patterns (15 min)**: 11 is discussion material. Ask students to identify the pattern in their own experience.

---

## Optional Challenge

After completing all demos, build a small report generator that:

1. Uses a `ReportRule` strategy to filter rows (e.g. `AmountAboveThreshold(500)`)
2. Uses a factory to load the rule from a config dict
3. Attaches a `PrintListener` observer that prints each accepted row

Starter config:
```python
rule_config = {"type": "amount_above", "threshold": 500}
rows = [{"id": 1, "amount": 200}, {"id": 2, "amount": 800}]
```

---

## Key Takeaways

- SOLID principles are design heuristics, not mandates — apply them where they reduce fragility.
- Patterns solve recurring collaboration problems; they are not about elegance for its own sake.
- Prefer composition over inheritance when the relationship is "has-a" or "uses-a".
- Factory + Strategy + Observer compose naturally — each manages a different axis of variation.
- The best time to apply these principles is when you notice a class has more than one reason to change.

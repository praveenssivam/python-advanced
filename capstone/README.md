# Capstone Project: Validify

**Enterprise Data Validation & Processing Service**

---

## The Story

You have inherited a single Python script — `starter/validate_trips.py` — that reads a
taxi trips CSV, runs a few hardcoded checks, and prints a report.

It works. But it is not maintainable, extensible, or testable.

Over five days you will **migrate this script** into a production-grade Python service
without rewriting it from scratch. Each migration step applies exactly what you learned
that day in theory:

| Day | Theory Modules | What changes in the project |
|-----|----------------|-----------------------------|
| 1 | OOP + Advanced OOP | Validation functions → class hierarchy with ABC |
| 2 | OOP + Advanced OOP | Plain classes → dataclasses + decorators + plugin registry |
| 3 | Design Patterns + FP | Hardcoded rules → config-driven factory + functional pipeline |
| 4 | Concurrency + Async | Sequential loop → threaded executor + FastAPI service |
| 5 | Testing + Git + Docker + CI | Unit tests, type hints, Git workflow, Docker, CI pipeline |

> **Time budget**: ~30–45 min per day (Part A is mandatory, Part B is stretch when time allows).

---

## Quick Start — Day 0 (Before Day 1 Theory)

```bash
# 1. Go to the starter script (data is already included)
cd capstone/starter/

# 2. Run the script
python validate_trips.py taxi_trips_sample.csv

# Try the extra flags
python validate_trips.py taxi_trips_sample.csv --verbose
python validate_trips.py taxi_trips_sample.csv --limit 50
python validate_trips.py taxi_trips_sample.csv --output failed.csv
```

Expected output:
```
============================================================
VALIDATION REPORT
============================================================
  Total records : 200
  Passed        : 100
  Failed        : 100
  Pass rate     : 50.0%

  Top failing fields:
    passenger_count                20 failures  (10.0%)
    vendor_id                      10 failures   (5.0%)
    payment_type                   10 failures   (5.0%)
    fare_amount                    10 failures   (5.0%)
    pickup_lat                     10 failures   (5.0%)

Failed rows (first 10):
  Row    3 | passenger_count: 0.0 is outside [1, 8]
  ...
============================================================
```

**Read `starter/validate_trips.py` before Day 1 starts.** You will not delete this code
— you will restructure it module by module.

---

## What You Are Building

By Day 5 these commands should all work:

```bash
cd validify/

# Set up once  (data/ already contains taxi_trips_sample.csv)
pip install -r requirements.txt -r requirements-dev.txt
# alternative: pip install -e ".[dev]"

# Run the evolving project directly
python -m validify.main data/taxi_trips_sample.csv

# Run as a REST service (Day 4+)
uvicorn validify.api.app:app --reload

# POST a file and GET the report
curl -X POST http://localhost:8000/validate -F "file=@data/taxi_trips_sample.csv"
curl http://localhost:8000/reports/<run_id>

# Quality gates (Day 5)
pytest --cov=src/validify --cov-fail-under=70
mypy src/
ruff check src/ tests/
docker build -t validify:local .
```

---

## Folder Structure

```
capstone/
├── README.md                          ← this file
├── starter/
│   └── validate_trips.py              ← Day 0: the script you start with
└── validify/                          ← the project you build toward
    ├── pyproject.toml                 ← GIVEN: deps + tool config
    ├── requirements.txt               ← GIVEN: runtime dependencies
    ├── requirements-dev.txt           ← GIVEN: dev/test dependencies
    ├── .gitignore                     ← GIVEN
    ├── config/
    │   └── rules.yaml                 ← GIVEN: declarative rule definitions
    ├── data/
    │   └── taxi_trips_sample.csv      ← GIVEN: 200-row dataset (clean + dirty rows)
    ├── src/
    │   └── validify/
    │       ├── core/
    │       │   ├── exceptions.py      ← GIVEN: complete exception hierarchy
    │       │   ├── models.py          ← YOU BUILD: Day 1 & 2
    │       │   └── base.py            ← YOU BUILD: Day 1 & 2
    │       ├── rules/
    │       │   ├── registry.py        ← YOU BUILD: Day 2
    │       │   └── built_in.py        ← YOU BUILD: Day 1 & 3
    │       ├── transforms/
    │       │   └── pipeline.py        ← YOU BUILD: Day 3
    │       ├── engine/
    │       │   └── runner.py          ← YOU BUILD: Day 4
    │       ├── api/
    │       │   └── app.py             ← YOU BUILD: Day 4
    │       ├── utils/
    │       │   └── decorators.py      ← YOU BUILD: Day 2
    │       └── main.py                ← YOU BUILD: Day 1 (replace starter script)
    ├── tests/
    │   ├── conftest.py                ← GIVEN: shared fixtures
    │   └── test_rules.py              ← YOU BUILD: Day 5
    ├── Dockerfile                     ← GIVEN skeleton: complete on Day 5
    └── .github/
        └── workflows/
            └── ci.yml                 ← GIVEN skeleton: complete on Day 5
```

---

## Daily Tasks

---

### Day 1 — OOP Refactor (45 min)

**Applies:** Module 1 (OOP) + Module 2 (Advanced Object Modeling, first half)

**Goal:** Convert the seven hardcoded validation *functions* in the starter script into
a *class hierarchy*.

**Setup (do this once before starting tasks):**
```bash
cd validify/
# data/ already contains taxi_trips_sample.csv
pip install -r requirements.txt -r requirements-dev.txt
# optional (modern approach): pip install -e ".[dev]"
```

**Part A — Mandatory (30 min):**

1. **`src/validify/core/base.py`** — implement `BaseValidator(ABC)`:
   - Abstract method: `validate(self, record: dict) -> bool`
   - Abstract property: `message(self) -> str`  (the error message when validation fails)
   - Concrete method: `__call__(self, record: dict) -> ValidationResult`
     that calls `validate()` and wraps the result in a `ValidationResult`

2. **`src/validify/core/models.py`** — implement `ValidationResult` as a **plain class**
   (not a dataclass yet — that is Day 2):
   - Fields: `field: str`, `rule: str`, `passed: bool`, `message: str`

3. **`src/validify/rules/built_in.py`** — implement three rules:
   - `NullCheckRule(BaseValidator)` — mirrors `check_not_null()`
   - `RangeRule(BaseValidator)` — mirrors `check_range()` (used for passenger_count, fare, distance)
   - `CoordinateRule(BaseValidator)` — mirrors `check_coordinate()` (same logic, named specifically)
   - Each rule stores `self.field` and any bounds/config in `__init__`

4. **`src/validify/main.py`** — create a minimal runner:
   ```python
   # load CSV, instantiate 3-4 rules, run __call__ on each record, print summary
   # does NOT need to fully match the starter script yet — coverage grows on Day 3
   ```

**Checkpoint:** `python src/validify/main.py data/taxi_trips_sample.csv` — runs without
errors and prints a validation report. (Full rule parity with the starter script is
achieved on Day 3 when rules load from `config/rules.yaml`.)

**Part B — Stretch (15 min):**
- Add `DateFormatRule(BaseValidator)` — mirrors `check_date_format()`
- Apply it to `pickup_datetime` and `dropoff_datetime` in `main.py`

---

### Day 2 — Advanced Object Modeling (45 min)

**Applies:** Module 2 (Advanced Object Modeling, second half)

**Goal:** Upgrade models to dataclasses, add decorators, make rules auto-register.

**Part A — Mandatory (30 min):**

1. **`core/models.py`** — convert `ValidationResult` to `@dataclass`.
   Add two more dataclasses:
   - `DataRecord(row_number: int, fields: dict[str, str])`
   - `Report(total: int, passed: int, failed: int, results: list[ValidationResult])`
     with a `@property pass_rate -> float`

2. **`utils/decorators.py`** — implement `@timeit`:
   - Prints `[timeit] <function_name> took 0.042s` after the function returns
   - Works on sync functions (async is a stretch)
   - Apply it to the main validation function in `main.py`

3. **`rules/registry.py`** — implement `ValidatorRegistry` using `__init_subclass__`:
   ```python
   class ValidatorRegistry:
       _registry: dict[str, type] = {}

       def __init_subclass__(cls, **kwargs):
           # register each subclass by its snake_case name
           ...

       @classmethod
       def get(cls, name: str) -> type:
           ...
   ```
   Make `BaseValidator` also inherit from `ValidatorRegistry` so that
   `NullCheckRule` and `RangeRule` register themselves automatically on import.

**Checkpoint:**
```python
from validify.rules.built_in import NullCheckRule  # import triggers registration
from validify.rules.registry import ValidatorRegistry

assert ValidatorRegistry.get("null_check_rule") is NullCheckRule
print("Registry works!")
```

**Part B — Stretch (15 min):**
- Add `@log_call` decorator to `utils/decorators.py` that logs the function name
  and its arguments (useful for debugging which rules run on which records)

---

### Day 3 — Design Patterns + Functional Pipeline (45 min)

**Applies:** Module 3 (Design Patterns) + Module 4 (Functional Programming)

**Goal:** Replace hardcoded rules with a config-driven factory. Add a transformation step
before validation runs.

**Part A — Mandatory (30 min):**

1. **`rules/built_in.py`** — add `RuleFactory` class (Factory pattern):
   ```python
   class RuleFactory:
       @staticmethod
       def from_config(path: str) -> list[BaseValidator]:
           # 1. read config/rules.yaml
           # 2. for each rule entry, call ValidatorRegistry.get(rule["type"])
           # 3. instantiate with the rule's parameters (field, min, max, etc.)
           # 4. return the list
   ```

2. **`main.py`** — replace the hardcoded `[NullCheckRule(...), RangeRule(...)]` list
   with `RuleFactory.from_config("config/rules.yaml")`.
   Adding a new rule now means editing only `config/rules.yaml`.

3. **`transforms/pipeline.py`** — implement:
   - `pipe(*fns)` using `functools.reduce`: `pipe(f, g, h)(x) == h(g(f(x)))`
   - `normalize_record(record: dict) -> dict` — strips whitespace from all string values

4. Add a `normalize_record` step before validation runs in `main.py`.

**Checkpoint:** Disable a rule in `config/rules.yaml` (comment it out or delete it).
Run `main.py` — confirm that rule no longer triggers. Restore it.

**Part B — Stretch (15 min):**
- Implement `DatasetLoader` as a context manager in `transforms/pipeline.py`:
  ```python
  with DatasetLoader("data/taxi_trips_sample.csv") as records:
      for record in records:   # generator, not a list
          ...
  ```
  Replace `open(csv_path, ...)` in `main.py` with this context manager.

---

### Day 4 — Concurrency + Async API (60 min)

**Applies:** Module 5 (Concurrency) + Module 6 (Async)

**Goal:** Run validation in parallel. Expose it as a REST endpoint.

**Part A — Mandatory (45 min):**

1. **`engine/runner.py`** — implement two execution functions:
   ```python
   def run_sequential(records, rules) -> list[ValidationResult]:
       # plain for-loop — baseline

   def run_threaded(records, rules, workers: int = 4) -> list[ValidationResult]:
       # ThreadPoolExecutor
       # use a Lock() to protect the shared results list
   ```
   Apply `@timeit` to both. After implementing, run both on the full CSV and note
   the elapsed times in a comment at the top of the file.

2. **`api/app.py`** — implement a minimal FastAPI app with three routes:
   ```
   GET  /health              → {"status": "ok", "version": "0.1.0"}
   POST /validate            → accepts UploadFile (CSV), runs run_threaded,
                               stores Report in an in-memory dict, returns {"run_id": "..."}
   GET  /reports/{run_id}    → returns the stored Report as JSON
   ```
   Use `uuid.uuid4()` for run IDs. Store reports in a module-level `dict`.

3. Test manually:
   ```bash
   uvicorn validify.api.app:app --reload

   curl http://localhost:8000/health

   curl -X POST http://localhost:8000/validate \
     -F "file=@data/taxi_trips_sample.csv"
   # → {"run_id": "abc-123", "summary": {"total": 200, "passed": 100, ...}}

   curl http://localhost:8000/reports/abc-123
   ```

**Part B — Stretch (15 min):**
- Implement `async def run_async(records, rules)` in `engine/runner.py` using
  `asyncio.gather`. Connect the `/validate` endpoint to this async engine instead.

---

### Day 5 — Testing, Typing, Git, Docker & CI (60 min)

**Applies:** Modules 7, 8, 9, 10, 11

**Goal:** Make the project reliable, typed, and releasable.

**Part A — Type hints + tests (35 min):**

1. Add type hints to `core/models.py`, `core/base.py`, `rules/built_in.py`.
   Run `mypy src/` and fix any errors.

2. **`tests/test_rules.py`** — write exactly 5 tests using `pytest`:
   - `test_null_check_passes_when_field_present`
   - `test_null_check_fails_when_field_empty`
   - `test_range_rule_passes_within_bounds`
   - `test_range_rule_fails_above_max`
   - `test_registry_has_null_check_rule`

3. Run: `pytest --cov=src/validify --cov-fail-under=70`

**Part B — Git workflow (10 min):**
```bash
git checkout -b feature/add-regex-rule

# Implement RegexRule(BaseValidator) in rules/built_in.py
# It takes field: str and pattern: str in __init__
# Add it to config/rules.yaml for the payment_type field

git add -A
git commit -m "feat: add RegexRule for payment_type validation"
git checkout main
git merge feature/add-regex-rule
git tag v1.0.0
```

**Part C — Docker + CI (15 min, stretch):**

Complete the `TODO` sections in `Dockerfile` and `.github/workflows/ci.yml`.
Then run:
```bash
docker build -t validify:local .
docker run --rm -p 8000:8000 validify:local
```

---

## Evaluation Checklist (End of Day 5)

- [ ] `python starter/validate_trips.py taxi_trips_sample.csv` — prints validation report
- [ ] `python src/validify/main.py data/taxi_trips_sample.csv` — same output, new structure
- [ ] Rules load from `config/rules.yaml` (removing a rule from YAML stops it running)
- [ ] `uvicorn validify.api.app:app` — server starts
- [ ] `POST /validate` + `GET /reports/{id}` return valid JSON
- [ ] `pytest tests/` — at least 5 tests, all green
- [ ] `mypy src/` — no errors
- [ ] `ruff check src/` — no errors
- [ ] `git log --oneline` — shows `feature/add-regex-rule` merge + `v1.0.0` tag
- [ ] (stretch) `docker build .` — succeeds

---

## Key Design Decisions

These are intentional simplifications — not shortcuts:

| Decision | Why |
|----------|-----|
| Reports stored in a module-level `dict` | No external dependencies; learning focus is on the Python patterns, not infrastructure |
| Single `main.py` runner file | Start simple; the API (Day 4) is a wrapper around the same logic |
| No auth on the API | Out of scope for this course; mention it as a production concern |
| `config/rules.yaml` not `config/rules.json` | YAML is more readable for non-developers who define rules |
| `ruff` instead of `flake8` + `black` + `isort` | One tool, fast, modern standard |

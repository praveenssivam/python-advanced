# Day 2 — Visual Reference: Advanced Object Modelling

---

## 01 — `__repr__`, `__str__`, `__eq__`

### Python string-representation dispatch chain

```mermaid
flowchart TD
    A["repr(obj)  /  f'{obj!r}'"] --> B["obj.__repr__()"]
    B --> C{defined?}
    C -- yes --> D["→ your string"]
    C -- no  --> E["object.__repr__()\n'&lt;ClassName at 0x…&gt;'"]

    F["str(obj)  /  print(obj)  /  f'{obj}'"] --> G["obj.__str__()"]
    G --> H{defined?}
    H -- yes --> I["→ your string"]
    H -- no  --> J["falls back to __repr__()"]

    K["items inside a list/dict\nprint([obj])"] --> L["uses repr() for each item"]
```

### Equality dispatch chain

```mermaid
flowchart LR
    A["a == b"] --> B["a.__eq__(b)"]
    B --> C{return value?}
    C -- "value"      --> R["→ result"]
    C -- NotImplemented --> D["b.__eq__(a)"]
    D --> E{return value?}
    E -- "value"      --> R
    E -- NotImplemented --> F["fall back to  a is b\n(identity)"]
```

### Before vs. After

| | No dunders | With `__repr__` + `__eq__` |
|---|---|---|
| `repr(obj)` | `<JobRunDefault object at 0x7f…>` | `JobRun(job_id='job-101', status='success', …)` |
| `print(obj)` | same as repr | `[SUCCESS] Job job-101 — 4500 records` |
| `obj1 == obj2` | `False` (identity) | `True` (field-by-field) |
| usable in set? | ❌ | ✅ (with `__hash__` too) |

---

## 02 — `@dataclass` Basics

### What `@dataclass` generates automatically

```mermaid
flowchart LR
    subgraph input["Class body you write"]
        F1["name: str"]
        F2["source: str"]
        F3["destination: str"]
        F4["parallelism: int = 4"]
    end

    DC["@dataclass\n(runs at import time)"]

    subgraph generated["Generated methods"]
        G1["__init__(name, source, destination,\n          parallelism=4)"]
        G2["__repr__()  →  PipelineConfig(name=…)"]
        G3["__eq__()  →  field-by-field compare"]
    end

    input --> DC --> generated
```

### Manual class vs. @dataclass — line count

```
PipelineConfigManual                PipelineConfig
─────────────────────────────       ─────────────────────────────
def __init__(self, ...):   6 lines  @dataclass
    self.name = name                class PipelineConfig:
    self.source = source                name: str
    ...                                 source: str
                                        destination: str
def __repr__(self):        8 lines      parallelism: int = 4
    return (...)

def __eq__(self, other):   8 lines  ← 5 lines total, same behaviour
    ...

Total: ~22 lines boilerplate
```

### `@dataclass` and `__hash__`

```mermaid
flowchart TD
    A["@dataclass"] --> B{frozen=True?}
    B -- yes --> C["__eq__ + __hash__ generated\n✅ usable in set / dict key"]
    B -- no  --> D["__eq__ generated\n__hash__ = None\n❌ not hashable by default"]
```

---

## 03 — Dataclass Field Defaults

### The mutable default trap

```mermaid
sequenceDiagram
    participant Py as Python parser
    participant Cls as StepBad class body
    participant s1 as s1 instance
    participant s2 as s2 instance

    Py->>Cls: parse class — create ONE list []
    Note over Cls: tags default = <SharedList>

    s1->>Cls: StepBad("extract")   → self.tags = <SharedList>
    s2->>Cls: StepBad("load")      → self.tags = <SharedList>

    s1->>s1: s1.tags.append("critical")
    Note over s2: s2.tags also shows ["critical"] 💥
```

### `field(default_factory=list)` — correct pattern

```mermaid
sequenceDiagram
    participant Py as Python
    participant dc as @dataclass generated __init__
    participant s1 as step1
    participant s2 as step2

    Py->>dc: PipelineStep("extract")
    dc->>s1: tags = list()  ← NEW list A
    Py->>dc: PipelineStep("transform")
    dc->>s2: tags = list()  ← NEW list B

    s1->>s1: step1.tags.append("critical")
    Note over s2: step2.tags = []  ✅ unaffected
```

### `field()` options reference

| Option | Effect | Use case |
|---|---|---|
| `default=v` | sets a fixed default value | scalars, constants |
| `default_factory=fn` | calls `fn()` per instance | lists, dicts, sets |
| `repr=False` | hides field from `__repr__` | large blobs, secrets |
| `init=False` | removes from `__init__` | computed/managed state |

### `frozen=True` effects

```mermaid
flowchart LR
    A["@dataclass(frozen=True)"] --> B["__setattr__ raises\nFrozenInstanceError"]
    A --> C["__hash__ is generated\n(hashable → usable in sets)"]
    A --> D["To 'change' a field:\nuse dataclasses.replace()"]
```

### `dataclasses.replace()` — copy-with-overrides

```
base = JobConfig("etl_daily")           # parallelism=4, timeout=300

replace(base, parallelism=16)
  ┌──────────────────────────────────┐
  │  name          = "etl_daily"  (copied)
  │  parallelism   = 16           (overridden)
  │  timeout_sec   = 300          (copied)
  │  retry         = True         (copied)
  └──────────────────────────────────┘
  → new JobConfig object   (base is UNCHANGED)
```

---

## 04 — Properties: Advanced

### Three property patterns side-by-side

```
PART 1: Computed (read-only)        PART 2: Validated setter           PART 3: Canonical store
────────────────────────────        ─────────────────────────          ────────────────────────
  _start ─┐                           self.hz = 100                      "  TRIP_DISTANCE  "
  _end   ─┴─► duration_sec               │                                       │
               (derived)              @hz.setter                         @name.setter
               no setter ─► AttributeError  │                             strips + lower
                             type check ─┘  │                             "trip_distance" → _name
                             range check    │                                  │
                             store _hz ◄───┘                           display_name property
                                                                        title-cases on read
```

### PART 1 — Computed property flow

```mermaid
flowchart LR
    A["w.duration_sec"] --> B["DataWindow.duration_sec\n.fget(w)"]
    B --> C["return self._end - self._start"]

    D["w.duration_sec = 100"] --> E["look for .fset"]
    E --> F["none defined\n→ AttributeError"]
```

### PART 2 — Validation setter flow

```mermaid
flowchart TD
    A["sr.hz = value\n(also fires in __init__)"] --> B["@hz.setter(value)"]
    B --> C{isinstance\nvalue, int?}
    C -- no  --> D["raise TypeError"]
    C -- yes --> E{MIN_HZ ≤ value\n≤ MAX_HZ?}
    E -- no  --> F["raise ValueError"]
    E -- yes --> G["self._hz = value ✅"]
    G --> H["period_ms = 1000 / _hz\n(always in sync)"]
```

### PART 3 — Stored vs. presented flow

```mermaid
flowchart LR
    input["'  TRIP_DISTANCE  '"] --> setter["@name.setter\nstrip + lower"]
    setter --> store["_name = 'trip_distance'"]
    store --> getter_raw["col.name → 'trip_distance'"]
    store --> getter_display["col.display_name\n→ 'Trip Distance'"]
```

### PART 4 — `__post_init__` in a dataclass

```mermaid
sequenceDiagram
    participant caller
    participant init as generated __init__
    participant post as __post_init__

    caller->>init: BudgetAllocation("Q1", {...})
    init->>init: self.name = "Q1"
    init->>init: self.allocations = {...}
    init->>post: self.__post_init__()
    post->>post: total = sum(values)
    alt total ≈ 100
        post-->>init: returns normally
        init-->>caller: returns object ✅
    else total ≠ 100
        post-->>caller: raises ValueError 💥
    end
```

---

## 05 — Context Managers

### The `with` statement protocol

```mermaid
sequenceDiagram
    participant caller
    participant ctx as Context Manager
    participant body as with-body

    caller->>ctx: __enter__()
    ctx-->>caller: returns value (bound to `as` var)
    caller->>body: execute body
    alt body completes normally
        body-->>ctx: __exit__(None, None, None)
        ctx-->>caller: returns (cleanup done)
    else body raises exception
        body-->>ctx: __exit__(ExcType, exc, tb)
        alt __exit__ returns True
            ctx-->>caller: exception SUPPRESSED ✅
        else __exit__ returns False/None
            ctx-->>caller: exception PROPAGATES 💥
        end
    end
```

### Class-based vs. `@contextmanager`

```
CLASS-BASED                         @contextmanager (generator)
───────────────────────             ───────────────────────────
class ManagedConnection:            @contextmanager
    def __enter__(self):            def managed_file_writer(path):
        open connection                 # === __enter__ ===
        return self                     handle = open(path, "w")
                                        try:
    def __exit__(self,                      yield handle   ← bound to `as`
            exc_type, exc_val,          finally:
            exc_tb):                        # === __exit__ ===
        close connection                    handle.close()
        return False
```

### Exception suppression in `__exit__`

```mermaid
flowchart TD
    A["exception raised in body"] --> B["__exit__(ExcType, exc, tb)"]
    B --> C{exc_type in\nallowed types?}
    C -- yes --> D["return True\n→ exception DISCARDED\nexecution resumes after with"]
    C -- no  --> E["return False\n→ exception PROPAGATES\nup the call stack"]
```

---

## 06 — Function Decorators

### The decorator pattern — what happens at definition time

```mermaid
flowchart LR
    A["def add(a, b): ..."] --> B["@make_loud\n(applies at definition time)"]
    B --> C["add = make_loud(add)"]
    C --> D["add  IS  wrapper\n(original func captured\nin closure)"]
```

### Call flow after decoration

```
add(3, 4)
  │
  ▼ wrapper(3, 4)          ← 'add' now refers to wrapper
    │
    ├─► print "→ calling add"
    │
    ├─► result = func(3, 4)  ← original add, captured by closure
    │       └─► returns 7
    │
    ├─► print "← add returned 7"
    │
    └─► return 7
```

### `functools.wraps` — what it copies

```mermaid
flowchart LR
    orig["original func\n__name__ = 'compute'\n__doc__  = 'Sum…'\n__module__, __qualname__"]
    wrapper["wrapper (without @wraps)\n__name__ = 'wrapper' ❌\n__doc__  = None ❌"]
    wrapped["wrapper (with @wraps)\n__name__ = 'compute' ✅\n__doc__  = 'Sum…' ✅\n__wrapped__ = original"]

    orig --> |"@functools.wraps(func)"| wrapped
    orig --> |"no wraps"| wrapper
```

### Decorator factory — three nesting levels

```
retry(max_attempts=3)         ← level 1: factory — configures the decorator
  └─► returns decorator(func) ← level 2: decorator — wraps the function
        └─► returns wrapper()  ← level 3: wrapper — runs on each call

@retry(max_attempts=3)
def flaky_fetch(url): ...

# equivalent to:
# flaky_fetch = retry(max_attempts=3)(flaky_fetch)
```

### Stacking decorators — application order

```
@log_call          ← applied SECOND (outermost)
@timing            ← applied FIRST  (innermost)
def process_batch(...): ...

# equivalent to:
# process_batch = log_call(timing(process_batch))

Runtime call order (top-down):
  process_batch(...)
    → log_call's wrapper     (prints CALL)
      → timing's wrapper     (starts timer)
        → original function  (does work)
      ← timing's wrapper     (prints elapsed)
    ← log_call's wrapper     (prints OK / ERROR)
```

---

## 07 — Class Decorators

### Class decorator flow

```mermaid
flowchart TD
    A["Python parses S3Extractor class body"] --> B["@register_component(kind='extractor')\nfires immediately"]
    B --> C["register_component('extractor')\nreturns decorator"]
    C --> D["decorator(S3Extractor)\ncalled"]
    D --> E["cls.component_kind = 'extractor'\ncls.component_name = 'S3Extractor'"]
    E --> F["returns cls unchanged\n(same class, now enriched)"]
    F --> G["S3Extractor.component_kind == 'extractor' ✅\nno inheritance required"]
```

### Three class decorator patterns

```
PATTERN 1: Add metadata          PATTERN 2: Inject a method       PATTERN 3: Enforce convention
─────────────────────────        ──────────────────────────        ────────────────────────────
@register_component("ext")       @add_describe                     @require_docstring
class S3Extractor: ...           class RunSummary: ...             class ValidatedStep: ...
  │                                │                                  │
  ▼                                ▼                                  ▼
stamps cls.component_kind        injects describe()                checks cls.__doc__
no inheritance needed            into class at def-time            raises TypeError BEFORE
                                 works like a regular method       any instance is created
```

### Class decorator vs. inheritance

```mermaid
flowchart LR
    subgraph decorator["Use class decorator when…"]
        D1["• Label / metadata needed\n  across unrelated classes"]
        D2["• Cross-cutting concern\n  (logging, validation)"]
        D3["• No IS-A relationship"]
    end

    subgraph inherit["Use inheritance when…"]
        I1["• Genuine IS-A relationship"]
        I2["• Subclasses override behaviour"]
        I3["• Enforcing an interface\n  (combine with ABC)"]
    end
```

---

## 08 — `__init_subclass__` Registry

### When does `__init_subclass__` fire?

```mermaid
sequenceDiagram
    participant Py as Python parser
    participant Base as Formatter (base)
    participant Sub as CSVFormatter (subclass)

    Py->>Sub: parse class CSVFormatter(Formatter, format_name="csv")
    Sub->>Base: Formatter.__init_subclass__(\n    cls=CSVFormatter,\n    format_name="csv")
    Base->>Base: check duplicate key
    Base->>Base: _registry["csv"] = CSVFormatter
    Base->>Base: CSVFormatter.format_name = "csv"
    Base-->>Py: registration complete ✅
    Note over Py: All this happens at class-definition\ntime — before any instance exists
```

### Registry state after all subclasses are defined

```
Formatter._registry
┌──────────────┬─────────────────────┐
│ "csv"        │ CSVFormatter        │
│ "json"       │ JSONFormatter       │
│ "markdown"   │ MarkdownFormatter   │
└──────────────┴─────────────────────┘

Formatter.get("csv")
  → looks up "csv" in _registry
  → finds CSVFormatter
  → calls CSVFormatter()
  → returns a fresh instance
```

### Key properties of the pattern

```mermaid
flowchart TD
    A["New subclass defined\nanywhere in the codebase"] --> B["__init_subclass__ fires\nimmediately"]
    B --> C["Class added to _registry\nunder its format_name key"]
    C --> D["Formatter base class\nNEVER needs to be modified"]
    D --> E["Lookup by string key:\nFormatter.get('csv')"]
```

### Comparison — manual registration vs. `__init_subclass__`

| | Manual registry | `__init_subclass__` |
|---|---|---|
| Where to register? | explicit `register(MyClass)` call | defining the class is enough |
| Forget to register? | ✅ easy to forget | ❌ impossible to forget |
| Base class changes? | must add registrar | never needs to change |
| Works across modules? | only if module is imported | same — must import the module |
| Duplicate detection? | manual | built-in (can add check) |

---

## 09 — Combined Modeling Demo

### How all Day 2 techniques compose

```mermaid
flowchart TD
    subgraph decorator["@timed (function decorator)"]
        T["wraps fetch() and filter_rows()\nrecords elapsed → timing_log"]
    end

    subgraph dc["@dataclass (JobResult)"]
        J["source, records_in, records_out\ntiming_log: dict"]
        JP["@property drop_rate\n@property drop_pct\n(computed, never stale)"]
        J --> JP
    end

    subgraph registry["__init_subclass__ (DataSource)"]
        R["InMemorySource → 'memory'\nGeneratedSource → 'generated'\nauto-registered at class-definition time"]
    end

    subgraph ctx["Context manager (PipelineSession)"]
        E["__enter__: record start time"]
        X["__exit__: compute total, print summary"]
    end

    subgraph job["FilterJob"]
        F["fetch()  ← @timed"]
        FR["filter_rows() ← @timed"]
    end

    registry --> job
    decorator --> job
    ctx --> job
    job --> dc
```

### Full execution flow — one pipeline run

```mermaid
sequenceDiagram
    participant caller
    participant session as PipelineSession (ctx mgr)
    participant job as FilterJob
    participant source as GeneratedSource
    participant result as JobResult (@dataclass)

    caller->>session: with PipelineSession("etl") as session
    session->>session: __enter__() — record start

    caller->>job: job = FilterJob(session)
    Note over job: timing_log shared with session

    caller->>job: job.run(source, min_value=7.5)

    job->>job: fetch(source)  ← @timed starts timer
    job->>source: source.fetch()
    source-->>job: raw rows
    job->>job: @timed stores timing_log["fetch"]

    job->>job: filter_rows(raw, 7.5)  ← @timed
    job->>job: filter by value >= 7.5
    job->>job: @timed stores timing_log["filter_rows"]

    job->>result: JobResult(source, records_in, records_out,\n             timing_log=...)
    result-->>job: instance with computed drop_rate

    job-->>caller: result
    caller->>session: exit with block
    session->>session: __exit__() — compute total ms
```

### Technique map

| Technique | Where in demo | Key behaviour |
|---|---|---|
| `@dataclass` | `JobResult` | auto `__init__`, `__repr__`, `__eq__`; `default_factory` for `timing_log` |
| `@property` | `drop_rate`, `drop_pct` | computed from `records_in/out`, never stale |
| Context manager | `PipelineSession` | `__enter__`/`__exit__`; cleans up even on error |
| Function decorator | `@timed` on `FilterJob` methods | wraps instance methods; duck-types `timing_log` |
| `__init_subclass__` | `DataSource` base | `InMemorySource` and `GeneratedSource` self-register |

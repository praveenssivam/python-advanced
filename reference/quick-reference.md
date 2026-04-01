# Advanced Python — Quick Reference

A module-by-module index of every key concept, pattern, and keyword with a one-line explanation.

---

## Module 1 · OOP Refresher & Code Design

| Keyword / Concept | One-Line Explanation |
|---|---|
| **Class** | A blueprint that defines state (attributes) and behaviour (methods) for objects. |
| **Instance** | A concrete object created from a class, with its own copy of instance attributes. |
| **Encapsulation** | Bundling data and the methods that operate on it inside a class, hiding internal details. |
| **`_single_underscore`** | Convention signalling "internal use" — not enforced by Python, but respected by developers. |
| **`__double_underscore`** (name mangling) | Prefix that makes an attribute harder to access from outside the class (`_ClassName__attr`). |
| **`@property`** | Decorator that exposes a method as a readable attribute, enabling computed or validated access. |
| **`@property.setter`** | Companion decorator that intercepts attribute assignment for validation or transformation. |
| **Inheritance** | A child class reuses and specialises behaviour from a parent class. |
| **`super()`** | Calls the next class in the MRO (Method Resolution Order), enabling cooperative inheritance. |
| **MRO (Method Resolution Order)** | The deterministic left-to-right order Python uses to look up methods in a class hierarchy. |
| **Method Overriding** | A subclass replaces an inherited method with its own implementation. |
| **Composition** | Building complex behaviour by combining small, focused objects rather than inheriting from them. |
| **"Favour composition over inheritance"** | Design principle: prefer object composition to reduce tight coupling and brittle hierarchies. |
| **Abstract Base Class (ABC)** | A class that defines a required interface and cannot be instantiated directly. |
| **`@abstractmethod`** | Decorator that marks a method as required on every concrete subclass. |
| **`abc.ABC`** | Convenient base class from the `abc` module that enables abstract method enforcement. |
| **Interface** | A contract (usually via ABC) that specifies what methods a class must implement. |
| **Designing for extension** | Writing code so new behaviour can be added without modifying existing code. |
| **God Class (anti-pattern)** | A class that knows too much and does too much — should be split by responsibility. |
| **Tight Coupling (anti-pattern)** | Two modules depend too closely on each other's internals, making change risky. |

---

## Module 2 · Advanced Object Modeling

| Keyword / Concept | One-Line Explanation |
|---|---|
| **Python Data Model** | The set of dunder methods Python calls internally to implement language syntax on objects. |
| **Dunder / Magic Method** | Double-underscore method (e.g. `__repr__`, `__len__`) that hooks into Python built-ins. |
| **`__repr__`** | Returns an unambiguous developer-facing string representation of an object. |
| **`__str__`** | Returns a human-friendly display string; falls back to `__repr__` if not defined. |
| **`__eq__`** | Defines equality comparison (`==`) between two objects. |
| **`__hash__`** | Returns an integer hash; must be consistent with `__eq__` for correct dict/set behaviour. |
| **`__len__`** | Makes an object respond to `len()`. |
| **`__getitem__`** | Makes an object subscriptable (`obj[key]`). |
| **`__contains__`** | Makes an object respond to the `in` operator. |
| **`@dataclass`** | Class decorator that auto-generates `__init__`, `__repr__`, `__eq__` from field annotations. |
| **`field(default_factory=...)`** | Provides a callable default for mutable dataclass fields (e.g. lists, dicts). |
| **`frozen=True`** | Dataclass option that makes all fields read-only (immutable after creation). |
| **Context Manager** | An object supporting `__enter__` / `__exit__` that wraps setup and teardown logic. |
| **`with` statement** | Syntax that invokes a context manager, guaranteeing cleanup even on exceptions. |
| **`@contextmanager`** | Decorator from `contextlib` for writing a context manager as a generator function. |
| **Function Decorator** | A wrapper function that adds behaviour (logging, timing, auth) to another function. |
| **`@functools.wraps`** | Preserves the original function's name, docstring, and signature inside a decorator. |
| **Class Decorator** | A decorator applied to an entire class to modify or wrap its behaviour. |
| **`__init_subclass__`** | Class method called automatically when a subclass is defined; used for plugin auto-registration. |
| **Plugin Registration** | Pattern where subclasses enrol themselves in a registry via `__init_subclass__`, enabling discovery without explicit listing. |

---

## Module 3 · Practical Design Patterns

| Keyword / Concept | One-Line Explanation |
|---|---|
| **SOLID** | Five object-oriented design principles that together produce flexible, maintainable code. |
| **SRP — Single Responsibility Principle** | A class should have exactly one reason to change. |
| **OCP — Open/Closed Principle** | Classes should be open for extension but closed for modification. |
| **LSP — Liskov Substitution Principle** | Subclasses must be usable wherever their parent type is expected without breaking behaviour. |
| **ISP — Interface Segregation Principle** | Prefer many small, focused interfaces over one large general one. |
| **DIP — Dependency Inversion Principle** | Depend on abstractions, not concrete implementations. |
| **Strategy Pattern** | Encapsulates interchangeable algorithms behind a common interface for runtime selection. |
| **Factory Pattern** | Centralises object creation logic, decoupling callers from concrete classes. |
| **Factory Method** | A method (or class) that returns an object of a type determined at runtime. |
| **Observer Pattern** | An object (subject) notifies a list of dependents (observers) when its state changes. |
| **Publish-Subscribe** | Generalised observer where publishers emit events and subscribers receive them without direct coupling. |
| **Dependency Injection** | Passing dependencies into a class from outside rather than creating them internally. |
| **Inversion of Control** | The principle that frameworks call your code rather than your code calling theirs. |
| **Anti-pattern** | A recurring solution that seems helpful but consistently makes things worse. |
| **Coupling** | The degree to which one module depends on another; lower is better. |
| **Cohesion** | The degree to which responsibilities within a module belong together; higher is better. |

---

## Module 4 · Functional Programming for Better Design

| Keyword / Concept | One-Line Explanation |
|---|---|
| **First-Class Function** | Functions are values: they can be passed as arguments, returned, or stored in variables. |
| **Higher-Order Function** | A function that takes or returns another function. |
| **Closure** | A function that captures variables from its enclosing scope, retaining them after the outer function exits. |
| **Pure Function** | A function with no side effects whose output depends only on its inputs. |
| **Immutability** | Data that cannot be changed after creation; avoids shared-state bugs. |
| **Function Composition** | Chaining functions so the output of one becomes the input of the next. |
| **`functools.partial`** | Creates a new function by pre-filling some arguments of an existing function. |
| **`functools.reduce`** | Applies a two-argument function cumulatively to a sequence, reducing it to a single value. |
| **`functools.lru_cache`** | Memoisation decorator that caches results of expensive function calls by their arguments. |
| **`map()`** | Applies a function to every element of an iterable, returning a lazy iterator. |
| **`filter()`** | Returns elements of an iterable for which a predicate function returns `True`. |
| **`lambda`** | An anonymous one-expression function defined inline. |
| **Generator Function** | Uses `yield` to lazily produce values one at a time, keeping memory usage low. |
| **Generator Expression** | A lazy version of a list comprehension: `(x*2 for x in items)`. |
| **`itertools`** | Standard library module of composable iterators (chain, product, islice, groupby, …). |
| **Memoisation** | Caching a function's return value for given inputs to avoid redundant computation. |
| **Pipeline** | A sequence of data-transforming functions applied one after another. |
| **Side Effect** | Any observable change a function makes beyond returning a value (I/O, mutation, state). |

---

## Module 5 · Concurrency for Real-World Applications

| Keyword / Concept | One-Line Explanation |
|---|---|
| **Concurrency** | Managing multiple tasks so they make progress — not necessarily at the same instant. |
| **Parallelism** | Executing multiple tasks simultaneously on separate CPU cores. |
| **GIL (Global Interpreter Lock)** | CPython's mutex that prevents multiple threads from executing Python bytecode simultaneously. |
| **I/O-bound task** | Work that spends most time waiting for external resources; threads help because GIL is released. |
| **CPU-bound task** | Work that spends most time computing; multiprocessing helps because it bypasses the GIL. |
| **Thread** | A lightweight unit of execution sharing memory space with other threads in the same process. |
| **`threading.Thread`** | Creates a new OS-level thread; suitable for I/O-bound tasks. |
| **`threading.Lock`** | A mutual exclusion primitive ensuring only one thread accesses shared state at a time. |
| **Race Condition** | A bug where two threads read and write shared data in an interleaved, unpredictable order. |
| **Deadlock** | Two or more threads each hold a lock the other needs, causing permanent standstill. |
| **Process** | An independent OS execution unit with its own memory space; immune to the GIL. |
| **`multiprocessing.Process`** | Spawns a new Python process; suitable for CPU-bound tasks. |
| **`concurrent.futures.ThreadPoolExecutor`** | Manages a pool of threads and returns `Future` objects for submitted work. |
| **`concurrent.futures.ProcessPoolExecutor`** | Same API as `ThreadPoolExecutor` but uses processes; useful for CPU-heavy work. |
| **`Future`** | A handle representing the eventual result of asynchronous work. |
| **`as_completed()`** | Iterator that yields `Future` objects in completion order, not submission order. |
| **`executor.map()`** | Applies a function to an iterable concurrently, returning results in input order. |
| **Shared State** | Data accessed by multiple threads/processes; requires explicit synchronisation. |
| **`queue.Queue`** | Thread-safe FIFO queue for passing data between producer and consumer threads. |

---

## Module 6 · Asynchronous Programming with asyncio

| Keyword / Concept | One-Line Explanation |
|---|---|
| **Async I/O** | Non-blocking I/O where a single thread handles many tasks by yielding while waiting. |
| **Event Loop** | The central asyncio scheduler that runs coroutines and I/O callbacks on a single thread. |
| **Coroutine** | An `async def` function that can be suspended at `await` points and resumed later. |
| **`async def`** | Defines a coroutine function; calling it returns a coroutine object, not a result. |
| **`await`** | Suspends the current coroutine until the awaitable completes, yielding control to the event loop. |
| **`asyncio.run()`** | Creates an event loop, runs a top-level coroutine to completion, then closes the loop. |
| **Task** | A wrapper around a coroutine that schedules it on the event loop and allows cancellation. |
| **`asyncio.create_task()`** | Schedules a coroutine as a Task, allowing it to run concurrently with the current coroutine. |
| **`asyncio.gather()`** | Runs multiple awaitables concurrently and collects all results. |
| **`asyncio.wait()`** | Runs awaitables concurrently; returns done/pending sets for fine-grained control. |
| **`asyncio.Semaphore`** | Limits the number of concurrent coroutines accessing a resource (rate limiting). |
| **Async Context Manager** | Implements `__aenter__` / `__aexit__` for use with `async with`. |
| **Async Generator** | Uses `yield` inside an `async def`; iterated with `async for`. |
| **`asyncio.sleep()`** | Non-blocking sleep that yields to the event loop, unlike `time.sleep()`. |
| **`asyncio.timeout()`** | Cancels an awaitable if it does not complete within the given seconds (Python 3.11+). |
| **`run_in_executor()`** | Runs a blocking (sync) function in a thread pool without blocking the event loop. |
| **Backpressure** | Mechanism to slow a producer when a consumer cannot keep up, preventing unbounded queues. |
| **`asyncio.Queue`** | Async-safe queue for coordinating producer/consumer coroutines. |

---

## Module 7 · Performance Engineering

| Keyword / Concept | One-Line Explanation |
|---|---|
| **Profiling** | Measuring where a program spends its time or allocates memory. |
| **Benchmarking** | Running code under controlled conditions to establish a performance baseline. |
| **`cProfile`** | Built-in deterministic profiler that records call counts, total time, and cumulative time. |
| **`pstats`** | Module for loading and sorting `.prof` files produced by `cProfile`. |
| **`ncalls`** | Profile column: number of times a function was called. |
| **`tottime`** | Profile column: time spent inside a function, excluding calls to sub-functions. |
| **`cumtime`** | Profile column: total time including all calls made by the function. |
| **`timeit`** | Standard library module that times a small code snippet by running it many times. |
| **`py-spy`** | Sampling profiler that attaches to a running Python process without code modification. |
| **Flame Graph** | Visualisation where bar width = time fraction; shows the full call stack at every sample. |
| **Hotspot** | The function or loop consuming the most time, identified by profiling. |
| **`lru_cache`** | Caches expensive function results; eliminates redundant repeated calls (see Module 4). |
| **`re.compile()`** | Pre-compiles a regex pattern to an object; avoids recompilation on every call. |
| **Generator (memory)** | Yields values lazily — processes one item at a time instead of loading all into memory. |
| **Algorithmic complexity** | Big-O characterisation of how runtime or memory scales with input size. |
| **Micro-optimisation** | Tuning low-level code details; only worthwhile after a hotspot has been identified. |
| **Memory profiling** | Tracking object allocation to find leaks or unnecessary large structures. |
| **Baseline** | The unoptimised performance number measured before any changes are made. |

---

## Module 8 · Testing, Typing & Reliability

| Keyword / Concept | One-Line Explanation |
|---|---|
| **Unit Test** | Tests a single function or class in isolation, with all dependencies replaced or controlled. |
| **Integration Test** | Tests the interaction between multiple real components. |
| **`pytest`** | The de-facto Python testing framework; discovers and runs tests with minimal boilerplate. |
| **`assert`** | `pytest`'s primary check; the framework rewrites it for detailed failure messages. |
| **Fixture** | Reusable setup/teardown logic annotated with `@pytest.fixture`; injected into tests by name. |
| **`conftest.py`** | Special file where shared fixtures are defined and automatically discovered by pytest. |
| **Parametrisation** | Running the same test function with multiple input sets via `@pytest.mark.parametrize`. |
| **Mocking** | Replacing a real dependency with a controllable fake to isolate the unit under test. |
| **`unittest.mock.Mock`** | An object that records all calls made to it and can be configured to return specific values. |
| **`unittest.mock.patch`** | Context manager / decorator that replaces a name in a module with a `Mock`. |
| **`MagicMock`** | A `Mock` subclass with pre-configured magic methods (`__len__`, `__iter__`, etc.). |
| **`pytest-asyncio`** | Plugin that enables testing of `async def` coroutines with `@pytest.mark.asyncio`. |
| **Coverage** | The percentage of source lines executed by the test suite; measured with `coverage.py`. |
| **`--cov` / `coverage report`** | CLI flags to produce a coverage report showing uncovered lines. |
| **Type Hint** | Annotation declaring the expected type of a variable, parameter, or return value. |
| **`mypy`** | Static type checker that validates type hints without running the code. |
| **`Protocol`** | Structural typing mechanism: any class implementing the required methods satisfies the interface. |
| **`TypeVar`** | A placeholder type used when writing generic functions or classes. |
| **`Optional[T]`** | Shorthand for `T \| None`; indicates a value may be absent. |
| **Structured Logging** | Emitting log records as key-value pairs or JSON rather than plain strings. |
| **`logging.Logger`** | Per-module logger; always create with `logging.getLogger(__name__)`. |
| **Exception Hierarchy** | Custom exceptions inheriting from a base `AppError` for fine-grained `except` clauses. |
| **`raise ... from`** | Chains exceptions, preserving the original traceback as context. |

---

## Module 9 · Git for Application Developers

| Keyword / Concept | One-Line Explanation |
|---|---|
| **Repository** | The version-controlled directory that stores every commit, branch, and tag. |
| **Commit** | A snapshot of changes with a message, author, and content hash. |
| **Branch** | A lightweight, movable pointer to a commit; enables parallel lines of development. |
| **`git merge`** | Integrates changes from one branch into another, creating a merge commit. |
| **`git rebase`** | Re-applies commits on top of a new base, producing a linear history. |
| **Fast-forward merge** | A merge where the target branch pointer simply moves forward; no merge commit created. |
| **3-way merge** | Merge using the two branch tips and their common ancestor; needed when histories diverge. |
| **Merge conflict** | Occurs when the same lines are changed differently on two branches; must be resolved manually. |
| **Pull Request (PR)** | A proposal to merge a branch; the unit of code review in team workflows. |
| **Feature Branch Workflow** | Each feature or fix lives in its own branch; merged to main via a PR. |
| **Git Flow** | Branching model with `main`, `develop`, `feature/*`, `release/*`, and `hotfix/*`. |
| **Trunk-Based Development** | Developers commit frequently to a single shared branch; relies on feature flags. |
| **`git cherry-pick`** | Applies a single commit from one branch onto another. |
| **`git stash`** | Temporarily shelves uncommitted changes so you can switch context. |
| **`git tag`** | A permanent, human-readable reference to a specific commit; used for releases. |
| **Semantic Versioning (SemVer)** | Version format `MAJOR.MINOR.PATCH`; MAJOR = breaking, MINOR = feature, PATCH = fix. |
| **`.gitignore`** | File listing patterns that Git should not track (build artefacts, secrets, venvs). |
| **`git bisect`** | Binary-search through commit history to find which commit introduced a bug. |
| **Squash merge** | Collapses all commits from a feature branch into one before merging. |
| **`CODEOWNERS`** | GitHub file mapping file paths to required reviewers for automatic review requests. |

---

## Module 10 · Docker for Python Applications

| Keyword / Concept | One-Line Explanation |
|---|---|
| **Container** | A lightweight, isolated runtime environment packaging an application with its dependencies. |
| **Image** | A read-only, layered filesystem snapshot used to create containers. |
| **`Dockerfile`** | Script of instructions that builds a Docker image layer by layer. |
| **Layer** | An immutable filesystem delta; layers are cached and reused across builds. |
| **`FROM`** | First Dockerfile instruction; specifies the base image. |
| **`COPY`** | Copies files from the host into the image at build time. |
| **`RUN`** | Executes a shell command during the image build and commits the result as a new layer. |
| **`CMD`** | Default command executed when a container starts (overridable at runtime). |
| **`ENTRYPOINT`** | Fixed command that always runs; `CMD` becomes its default arguments. |
| **Multi-stage build** | Uses multiple `FROM` statements to build in one stage and copy only artefacts to a smaller final image. |
| **`.dockerignore`** | Lists files to exclude from the build context, keeping images lean. |
| **Build context** | The directory sent to the Docker daemon; smaller context = faster builds. |
| **`docker build`** | Creates an image from a `Dockerfile`. |
| **`docker run`** | Creates and starts a container from an image. |
| **`docker compose`** | Tool for defining and running multi-container applications from a `compose.yml` file. |
| **Port mapping (`-p`)** | Maps a host port to a container port: `-p 8080:80`. |
| **Volume** | A persistent storage path mounted into a container, surviving container restarts. |
| **Environment variable (`ENV`, `-e`)** | Passes runtime configuration into a container without baking it into the image. |
| **Health check (`HEALTHCHECK`)** | Defines a command Docker runs periodically to verify the container is healthy. |
| **Base image** | The starting image in `FROM`; prefer slim or distroless variants for smaller attack surfaces. |
| **`python:3.12-slim`** | Official Python image with only essential OS packages; significantly smaller than the full image. |

---

## Module 11 · CI/CD from Developer Perspective

| Keyword / Concept | One-Line Explanation |
|---|---|
| **CI (Continuous Integration)** | Automatically build and test every commit so integration issues are caught immediately. |
| **CD (Continuous Delivery)** | Automatically prepare a tested, deployable artefact after every passing CI run. |
| **CD (Continuous Deployment)** | Goes one step further — automatically deploy passing builds to production. |
| **Pipeline** | An ordered sequence of automated stages (lint → test → build → deploy). |
| **Stage / Job** | A logical unit of pipeline work that runs on a specific runner or worker. |
| **GitHub Actions** | CI/CD platform integrated into GitHub; pipelines are defined in `.github/workflows/*.yml`. |
| **Workflow** | A GitHub Actions YAML file triggered by events (push, PR, schedule). |
| **Trigger (`on:`)** | Specifies which GitHub event starts the workflow (e.g. `push`, `pull_request`). |
| **Runner** | The virtual machine or container that executes workflow jobs. |
| **`ubuntu-latest`** | GitHub-hosted Linux runner; the most common runner for Python projects. |
| **Step** | A single task within a job: a shell command or a reusable Action. |
| **Action (`uses:`)** | A reusable, versioned unit of CI work (e.g. `actions/checkout@v4`, `actions/setup-python@v5`). |
| **`actions/checkout`** | Action that clones the repository into the runner's workspace. |
| **`actions/setup-python`** | Action that installs a specific Python version on the runner. |
| **Lint stage** | Runs style and static analysis tools (`ruff`, `flake8`, `mypy`) to catch issues before tests. |
| **Test stage** | Runs `pytest` (with coverage) to validate behaviour. |
| **Build stage** | Compiles artefacts or builds the Docker image. |
| **Artefact** | Any file output from a pipeline stage (wheel, Docker image, coverage report). |
| **`ruff`** | Fast Python linter and formatter (replaces `flake8`, `isort`, `pyupgrade`). |
| **`flake8`** | PEP-8 style and error checker. |
| **Matrix strategy** | Runs a job multiple times across a combination of values (e.g. Python 3.11, 3.12, 3.13). |
| **Cache (`actions/cache`)** | Saves and restores pip or venv directories across runs to speed up installs. |
| **Secret (`secrets.*`)** | Encrypted value stored in GitHub, injected as an environment variable at runtime. |
| **Coverage gate** | CI step that fails the build if test coverage falls below a defined threshold. |

---

## Cross-Cutting Concepts

| Keyword / Concept | One-Line Explanation |
|---|---|
| **DRY (Don't Repeat Yourself)** | Every piece of knowledge should have a single, authoritative representation. |
| **YAGNI (You Aren't Gonna Need It)** | Don't implement something until it is actually needed. |
| **KISS (Keep It Simple, Stupid)** | Prefer the simplest solution that correctly solves the problem. |
| **Separation of Concerns** | Different responsibilities should live in different modules or classes. |
| **Abstraction** | Hiding implementation details behind a simple, stable interface. |
| **Technical Debt** | The future cost of shortcuts taken now; accumulates interest over time. |
| **Refactoring** | Improving code structure without changing external behaviour. |
| **Code Smell** | A surface-level symptom that often points to a deeper design problem. |
| **Idiomatic Python ("Pythonic")** | Code that follows Python conventions and leverages the language naturally. |
| **`__init__.py`** | Makes a directory a Python package; can re-export names for a clean public API. |
| **`__main__.py`** | Makes a package runnable with `python -m <package>`. |
| **`pyproject.toml`** | Unified project metadata, build configuration, and tool settings file (PEP 517/518). |
| **Virtual environment (`.venv`)** | An isolated directory containing a project-specific Python interpreter and packages. |
| **`pip install -e .`** | Installs a package in editable mode so changes are reflected without reinstalling. |
| **Typing: `Any`** | Opts out of type checking for a value; use sparingly at real boundaries only. |
| **`__slots__`** | Explicitly declares instance attributes, reducing per-object memory overhead. |

# Module 8 — Testing & Reliability

## Learning Goals

After this module you can:
- Describe the **testing pyramid** and assign each test to the right layer
- Write unit tests with `unittest.TestCase` and plain `pytest` functions
- Use `@pytest.fixture` with `yield` for setup/teardown and dependency injection
- Write parametrized tests with `@pytest.mark.parametrize` and named IDs
- Mock external dependencies with `mocker.patch.object()`
- Test exception paths with `pytest.raises` and `match=r"..."`
- Write property-based tests with `@given(st.text())` and Hypothesis
- Implement a **retry decorator** with exponential backoff + jitter
- Read a `pytest --cov` coverage report and add the missing tests
- Compose all patterns into a complete production test suite

---

## The Testing Pyramid

```
           /\
          /  \
         / E2E\         ← Few — slow, expensive, test full system
        /------\
       /  Integ  \      ← Moderate — two components together
      /------------\
     /  Unit Tests   \  ← Many — fast, isolated, mocked dependencies
    /----------------\
```

**70% unit · 20% integration · 10% E2E** — push tests as far down the pyramid as they can validly go.

---

## Key Patterns

### pytest vs unittest

| Feature | `unittest` | `pytest` |
|---|---|---|
| Assertion style | `self.assertEqual(a, b)` | `assert a == b` |
| Failure message | `"False is not true"` | shows actual/expected values |
| Setup/teardown | `setUp` / `tearDown` per class | composable `@pytest.fixture` |
| Parametrize | manual loop or `subTest` | `@pytest.mark.parametrize` |
| Discovery | must inherit `TestCase` | any `def test_*()` |
| Plugins | limited | 1000+ (`cov`, `asyncio`, `mock`, …) |

### Fixture Scopes

| Scope | Lifetime | Use for |
|---|---|---|
| `function` (default) | one per test | isolated unit tests |
| `class` | one per TestCase class | shared class state |
| `module` | one per `.py` file | DB connections |
| `session` | one per `pytest` run | expensive global setup |

### Mock API Quick Reference

```python
mocker.patch.object(obj, "method")    # safest — no string path
mock.return_value = X                  # always return X
mock.side_effect = Exception()         # always raise
mock.side_effect = [a, b, c]          # sequence: a on 1st call, b on 2nd, …
mock.assert_called_once_with(X)        # assert called exactly once with X
mock.assert_not_called()               # assert never called
mock.call_count                        # number of calls
mock.call_args.args / .kwargs          # inspect last call arguments
```

Patch target rule: patch **where the name is used**, not where it is defined.

### Retry Backoff Formula

$$\text{delay} = \min(\text{base} \times 2^{\text{attempt}},\ \text{max\_delay}) + \text{jitter}$$

Jitter is uniform random in `[0, delay × 10%]` — prevents thundering herd.

---

## Hypothesis: Property-Based Testing

```python
from hypothesis import given, settings
from hypothesis import strategies as st

@given(st.text(min_size=0, max_size=200))
@settings(max_examples=200)
def test_my_invariant(s):
    result = my_function(s)
    assert isinstance(result, str)   # invariant holds for ALL inputs
```

Hypothesis generates 100+ random inputs, finds a failing one, then **shrinks** it to the minimal counterexample.

| Strategy | Generates |
|---|---|
| `st.text()` | any Unicode string |
| `st.integers(min_value=1)` | positive integers |
| `st.emails()` | valid email addresses |
| `st.dates()` | valid `date` objects |
| `st.lists(st.integers())` | lists of integers |
| `st.fixed_dictionaries({...})` | dict with typed keys |

---

## Files

| File | Topic | Key Concepts |
|---|---|---|
| [01_unittest_basics.py](01_unittest_basics.py) | `unittest.TestCase` | `setUp`, `tearDown`, `subTest`, assertion methods |
| [02_pytest_basics.py](02_pytest_basics.py) | pytest vs unittest | plain `assert`, failure messages, discovery |
| [03_fixtures.py](03_fixtures.py) | Fixtures | `@pytest.fixture`, `yield`, fixture injection, scopes |
| [04_parametrize.py](04_parametrize.py) | Parametrize | `@pytest.mark.parametrize`, `pytest.param(id=...)`, cartesian product |
| [05_mocking.py](05_mocking.py) | Mocking | `mocker.patch.object`, `return_value`, `side_effect`, call assertions |
| [06_exception_testing.py](06_exception_testing.py) | Exception paths | `pytest.raises`, `match=`, `exc_info.value`, parametrized exception tests |
| [07_hypothesis.py](07_hypothesis.py) | Hypothesis | `@given`, strategies, `assume()`, `@xfail` bug demo, shrinking |
| [08_retry_decorator.py](08_retry_decorator.py) | Retry + backoff | `@retry` decorator, exponential backoff, jitter, test with mocked sleep |
| [09_coverage.py](09_coverage.py) | Coverage | `--cov`, `term-missing`, `pragma: no cover`, `--cov-fail-under` |
| [10_full_test_suite.py](10_full_test_suite.py) | Full suite | All patterns: happy path, edge cases, exceptions, batch, async, property |

---

## Run Commands

```bash
# Run a single file (runs pytest internally):
python demo/module-08/01_unittest_basics.py

# Run all files directly via pytest:
pytest demo/module-08/ -v

# Run async tests explicitly:
pytest demo/module-08/10_full_test_suite.py -v --asyncio-mode=auto

# Coverage report:
pytest demo/module-08/09_coverage.py -v \
    --cov=demo/module-08/09_coverage --cov-report=term-missing

# Run only Hypothesis tests:
pytest demo/module-08/07_hypothesis.py -v

# See Hypothesis find the bug (remove @xfail to activate):
pytest demo/module-08/07_hypothesis.py::test_normalize_BUGGY_no_control_chars -v
```

---

## Trainer Flow (5 sessions)

| Session | File | Focus |
|---|---|---|
| T1 — Pyramid & unittest | `01`, `02` | Why test, unittest vs pytest, reading output |
| T2 — Fixtures & Parametrize | `03`, `04` | Fixture injection, scope, named test IDs |
| T3 — Mocking & Exceptions | `05`, `06` | Isolate dependencies, assert call args, exception message tests |
| T4 — Hypothesis & Retry | `07`, `08` | Property invariants, shrinking demo, backoff math |
| T5 — Coverage & Full Suite | `09`, `10` | Reading missing lines, CI threshold, composing all patterns |

---

## Dependencies

```bash
pip install pytest pytest-mock pytest-asyncio pytest-cov hypothesis
```

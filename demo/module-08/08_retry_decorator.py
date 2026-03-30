"""
08_retry_decorator.py
=====================
Reliability: retry with exponential backoff + jitter.

Topics:
  1. @retry decorator — wraps any function with automatic retry logic
  2. Exponential backoff: delay doubles each attempt; capped at max_delay
  3. Jitter: random noise prevents thundering-herd when N services retry at once
  4. Testing: mock a service that fails twice then succeeds  (no real sleeping)
  5. Idempotency note — retries are only safe on idempotent operations

Run:
    python demo/module-08/08_retry_decorator.py
    pytest demo/module-08/08_retry_decorator.py -v
"""

import sys
import time
import random
from functools import wraps

import pytest


# ══════════════════════════════════════════════════════════════════════════════
# RETRY DECORATOR
# ══════════════════════════════════════════════════════════════════════════════

def retry(
    max_attempts: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 10.0,
    exceptions: tuple = (Exception,),
):
    """
    Retry decorator with exponential backoff + jitter.

    Parameters
    ----------
    max_attempts : total number of attempts (1 = no retry)
    base_delay   : initial wait in seconds; doubles each attempt
    max_delay    : cap on the computed delay
    exceptions   : only retry on these exception types; others propagate immediately

    Delay formula: min(base_delay * 2^attempt, max_delay) + jitter
    Jitter       : uniform random in [0, delay * 0.1]
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return fn(*args, **kwargs)
                except exceptions as exc:
                    if attempt == max_attempts - 1:
                        raise                           # re-raise on final attempt
                    delay  = min(base_delay * (2 ** attempt), max_delay)
                    jitter = random.uniform(0.0, delay * 0.1)
                    time.sleep(delay + jitter)
        return wrapper
    return decorator


# ══════════════════════════════════════════════════════════════════════════════
# PRODUCTION CODE that uses the decorator
# ══════════════════════════════════════════════════════════════════════════════

class ExternalService:
    """Simulates an unstable remote API."""

    def fetch_record(self, record_id: int) -> dict:
        raise NotImplementedError("replace with a real HTTP/DB call")

    def write_record(self, record: dict) -> None:
        raise NotImplementedError


_svc = ExternalService()


@retry(max_attempts=3, base_delay=0.001, exceptions=(ConnectionError, TimeoutError))
def fetch_with_retry(record_id: int) -> dict:
    """Fetch a record from the unstable service; retry on transient errors."""
    return _svc.fetch_record(record_id)


# ══════════════════════════════════════════════════════════════════════════════
# TESTS
#
# Key pattern: mock time.sleep to prevent actual waiting in CI,
# then inspect the sleep calls to verify backoff math.
# ══════════════════════════════════════════════════════════════════════════════

def test_success_on_first_attempt(mocker):
    """Service succeeds immediately — called exactly once, no sleep."""
    mock_fetch = mocker.patch.object(_svc, "fetch_record")
    mock_fetch.return_value = {"id": 1, "name": "Alice"}

    result = fetch_with_retry(1)

    assert result == {"id": 1, "name": "Alice"}
    mock_fetch.assert_called_once_with(1)


def test_succeeds_after_two_failures(mocker):
    """
    Service fails twice (ConnectionError) then succeeds.
    Expected: result is correct, service called 3 times total.
    """
    mocker.patch("time.sleep")                # prevent real waiting
    mock_fetch = mocker.patch.object(_svc, "fetch_record")
    mock_fetch.side_effect = [
        ConnectionError("timeout"),
        ConnectionError("timeout"),
        {"id": 2, "name": "Bob"},             # 3rd attempt succeeds
    ]

    result = fetch_with_retry(2)

    assert result == {"id": 2, "name": "Bob"}
    assert mock_fetch.call_count == 3


def test_raises_after_all_attempts_exhausted(mocker):
    """All 3 attempts fail — final ConnectionError is re-raised."""
    mocker.patch("time.sleep")
    mock_fetch = mocker.patch.object(_svc, "fetch_record")
    mock_fetch.side_effect = ConnectionError("persistent failure")

    with pytest.raises(ConnectionError, match="persistent failure"):
        fetch_with_retry(3)

    assert mock_fetch.call_count == 3         # tried exactly 3 times


def test_non_retryable_exception_propagates_immediately(mocker):
    """
    ValueError is not in the exceptions tuple — it must NOT be retried.
    The decorator should let it propagate on the first failure.
    """
    mock_fetch = mocker.patch.object(_svc, "fetch_record")
    mock_fetch.side_effect = ValueError("bad record_id format")

    with pytest.raises(ValueError):
        fetch_with_retry("bad")

    mock_fetch.assert_called_once()           # called once, not retried


def test_backoff_delays_increase_exponentially(mocker):
    """
    Verify time.sleep is called with exponentially increasing delays.
    Uses a custom @retry with 4 attempts so we see 3 sleeps.
    """
    sleep_mock = mocker.patch("time.sleep")

    @retry(max_attempts=4, base_delay=1.0, max_delay=100.0,
           exceptions=(ConnectionError,))
    def unstable():
        return _svc.fetch_record(99)

    mock_fetch = mocker.patch.object(_svc, "fetch_record")
    mock_fetch.side_effect = [
        ConnectionError(), ConnectionError(), ConnectionError(),
        {"id": 99},
    ]

    unstable()

    delays = [c.args[0] for c in sleep_mock.call_args_list]
    assert len(delays) == 3
    # base=1.0: attempt 0 → ≥1.0s, attempt 1 → ≥2.0s, attempt 2 → ≥4.0s
    assert delays[0] >= 1.0
    assert delays[1] >= 2.0
    assert delays[2] >= 4.0


def test_retry_respects_max_delay_cap(mocker):
    """Delay must never exceed max_delay regardless of attempt number."""
    sleep_mock = mocker.patch("time.sleep")

    @retry(max_attempts=5, base_delay=10.0, max_delay=15.0,
           exceptions=(ConnectionError,))
    def capped():
        return _svc.fetch_record(0)

    mock_fetch = mocker.patch.object(_svc, "fetch_record")
    mock_fetch.side_effect = [
        ConnectionError(), ConnectionError(), ConnectionError(), ConnectionError(),
        {"id": 0},
    ]
    capped()

    delays = [c.args[0] for c in sleep_mock.call_args_list]
    # Uncapped: 10, 20, 40, 80 — with cap=15: all must be ≤ 15 + 10% jitter
    for d in delays:
        assert d <= 15.0 * 1.11     # 15s + maximum 10% jitter


# ══════════════════════════════════════════════════════════════════════════════
# DEMO: backoff table + concepts
# ══════════════════════════════════════════════════════════════════════════════

def demo_backoff_table() -> None:
    print("\n" + "═" * 78)
    print("  EXPONENTIAL BACKOFF — DELAY TABLE  (base=0.5s, max=10s)")
    print("═" * 78)
    print()
    print(f"  {'Attempt':<8}  {'Formula':<22}  {'Delay':<8}  Bar")
    print(f"  {'-'*8}  {'-'*22}  {'-'*8}  ---")
    base = 0.5
    for i in range(6):
        delay = min(base * (2 ** i), 10.0)
        bar   = "█" * int(delay * 3)
        capped = " (capped)" if base * (2 ** i) > 10.0 else ""
        print(f"  {i:<8}  {base}×2^{i} = {base*(2**i):.1f}s{'':<7}  "
              f"{delay:<8.2f}  {bar}{capped}")
    print()
    print("  Why jitter?  Without it, all retrying clients wake up at the")
    print("  same moment (thundering herd) and overload the service again.")
    print("  Adding uniform noise in [0, delay×10%] spreads them out.")
    print()
    print("  Idempotency requirement:")
    print("    Retries are ONLY safe when the operation is idempotent —")
    print("    running it twice has the same effect as running it once.")
    print("    Use INSERT ... ON CONFLICT, PUT (not POST), or idempotency keys.")
    print()


def main() -> None:
    demo_backoff_table()

    print("═" * 78)
    print("  RUNNING RETRY TESTS")
    print("═" * 78)
    print()
    ret = pytest.main([__file__, "-v", "--tb=short", "--no-header"])
    sys.exit(ret)


if __name__ == "__main__":
    main()

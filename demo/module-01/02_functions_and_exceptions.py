"""
02_functions_and_exceptions.py
================================
Demonstrates function parameters, default values, return values,
local scope, and exception handling with try/except/else/finally.

Run:
    python module-01/02_functions_and_exceptions.py
"""


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1: Parameters and return values
#
# Python function parameters can have DEFAULT VALUES, making them optional.
# Arguments can be passed POSITIONALLY or by KEYWORD name.
# A function may have multiple return paths; always returns exactly one value
# (or None if there is no return statement).
#
# Flow for  calculate_discount(200, 25):
#   1. price=200, discount_pct=25
#   2. Validate 0 <= 25 <= 100  → passes
#   3. reduction = 200 * (25/100) = 50.0
#   4. return 200 - 50.0 = 150.0
#
# Flow for  calculate_discount(200):
#   1. price=200, discount_pct=10  (default applied)
#   2–4 same as above → return 180.0
# ══════════════════════════════════════════════════════════════════════════════

# ── Parameters and return values ────────────────────────────────────────────

def calculate_discount(price, discount_pct=10):
    """Return price after applying a percentage discount.

    discount_pct defaults to 10 if not provided.
    """
    if not (0 <= discount_pct <= 100):
        raise ValueError(f"discount_pct must be 0–100, got {discount_pct}")
    reduction = price * (discount_pct / 100)
    return price - reduction


def demo_parameters():
    print("=" * 50)
    print("SECTION 1: Parameters and default values")
    print("=" * 50)

    print(calculate_discount(200))           # uses default 10%
    print(calculate_discount(200, 25))       # explicit 25%
    print(calculate_discount(200, discount_pct=50))  # keyword argument


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2: Local scope and closures
#
# Each function call creates its own LOCAL SCOPE — a namespace for names
# defined inside that call.  Names in the local scope shadow outer names.
# A CLOSURE is a function that captures names from its enclosing scope;
# it can READ the enclosing name but cannot REBIND it (without `nonlocal`).
#
# Flow for  rate = 0.05; def apply_rate(amount): return amount * (1+rate):
#   1. rate = 0.05 exists in demo_scope's local scope
#   2. apply_rate captures 'rate' from the enclosing scope (closure)
#   3. apply_rate(1000) → amount=1000; reads rate=0.05 → returns 1050.0
#
# Flow for  outer = "original"; def modify(): outer = "local copy":
#   1. outer = "original" exists in demo_scope's scope
#   2. Inside modify(), 'outer = ...' creates a NEW local, shadowing the outer one
#      It does NOT modify the outer binding — outer stays "original"
# ══════════════════════════════════════════════════════════════════════════════

# ── Local scope ───────────────────────────────────────────────────────────────────────────

def demo_scope():
    print("\n" + "=" * 50)
    print("SECTION 2: Local scope")
    print("=" * 50)

    rate = 0.05  # this is a local variable — it shadows nothing here

    def apply_rate(amount):
        # rate here is read from the enclosing scope (closure)
        return amount * (1 + rate)

    print(f"apply_rate(1000) = {apply_rate(1000)}")
    print(f"rate in outer scope is still: {rate}")

    # Local reassignment inside a function does not affect the outer name
    outer = "original"

    def modify():
        outer = "local copy"  # noqa: F841 — creates a new local, outer unchanged
        return outer

    modify()
    print(f"\nouter after modify() = '{outer}'")
    print("Reassignment inside modify() created a new local — outer is unchanged.")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3: try / except / else / finally
#
# try         → code that might raise an exception
# except E as e→ runs ONLY if an exception of type E (or subtype) is raised
# else         → runs ONLY if NO exception was raised in try
# finally      → ALWAYS runs: cleanup — close files, release locks, etc.
#
# Flow for  parse_sensor_reading("23.7"):
#   1. try: float("23.7") → 23.7   (no exception)
#   2.      23.7 < 0? No → return 23.7
#   3. except: SKIPPED
#   4. else:   runs → prints "Valid reading: 23.7"
#   5. finally: ALWAYS runs → prints "Finished processing '23.7'"
#
# Flow for  parse_sensor_reading("-5.1"):
#   1. try: float("-5.1") → -5.1
#   2.      -5.1 < 0 → raise ValueError("Sensor reading cannot be negative")
#   3. except ValueError: runs → prints "Invalid reading — ..."
#   4. else: SKIPPED
#   5. finally: ALWAYS runs → prints "Finished processing '-5.1'"
# ══════════════════════════════════════════════════════════════════════════════

# ── Exception handling ────────────────────────────────────────────────────────────────────

def parse_sensor_reading(raw_value):
    """Convert a string sensor reading to float. Raises ValueError on bad input."""
    value = float(raw_value)  # raises ValueError if raw_value is not numeric
    if value < 0:
        raise ValueError(f"Sensor reading cannot be negative: {value}")
    return value


def demo_exceptions():
    print("\n" + "=" * 50)
    print("SECTION 3: try / except / else / finally")
    print("=" * 50)

    test_cases = ["23.7", "-5.1", "bad_data", "0.0"]

    for raw in test_cases:
        print(f"\n  Processing raw value: {raw!r}")
        try:
            reading = parse_sensor_reading(raw)
        except ValueError as e:
            # Runs only when an exception is raised in the try block
            print(f"  [except]  Invalid reading — {e}")
        else:
            # Runs only when NO exception was raised
            print(f"  [else]    Valid reading: {reading}")
        finally:
            # Always runs — good for cleanup (closing files, releasing locks, etc.)
            print(f"  [finally] Finished processing {raw!r}")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4: Raising exceptions with descriptive messages
#
# Use  raise ExceptionType("message")  to signal an error explicitly.
# Choose the most specific built-in type that fits the situation:
#   ValueError   → right type, wrong value / range / format
#   TypeError    → wrong type entirely
#   KeyError     → required dict key is missing
#   RuntimeError → logic failure with no better fit
#
# Flow for  load_pipeline_config({"source": "s3://..."})  (incomplete config):
#   1. required_keys = ["source", "destination", "format"]
#   2. missing = ["destination", "format"]  (not in config)
#   3. missing is truthy → raise KeyError("Missing required config keys: [...]")
#   4. Caller catches KeyError and prints the error message
# ══════════════════════════════════════════════════════════════════════════════

# ── Raising and re-raising ─────────────────────────────────────────────────────────

def load_pipeline_config(config: dict):
    """Extract required keys from a configuration dictionary."""
    required_keys = ["source", "destination", "format"]
    missing = [k for k in required_keys if k not in config]
    if missing:
        raise KeyError(f"Missing required config keys: {missing}")
    return config


def demo_raising():
    print("\n" + "=" * 50)
    print("SECTION 4: Raising exceptions with context")
    print("=" * 50)

    valid_config = {"source": "s3://bucket/raw", "destination": "s3://bucket/clean", "format": "parquet"}
    incomplete_config = {"source": "s3://bucket/raw"}

    try:
        cfg = load_pipeline_config(valid_config)
        print(f"Loaded config: {cfg}")
    except KeyError as e:
        print(f"Config error: {e}")

    try:
        load_pipeline_config(incomplete_config)
    except KeyError as e:
        print(f"Config error: {e}")


def main():
    demo_parameters()
    demo_scope()
    demo_exceptions()
    demo_raising()


if __name__ == "__main__":
    main()

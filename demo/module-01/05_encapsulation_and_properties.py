"""
05_encapsulation_and_properties.py
====================================
Demonstrates encapsulation conventions (_name, __name), controlled
attribute access via @property, and validation through a property
setter. Uses a temperature sensor reading as the domain example.

Run:
    python module-01/05_encapsulation_and_properties.py
"""


# ══════════════════════════════════════════════════════════════════════════════
# PART 1: No encapsulation — open to invalid state
#
# When all attributes are public, any caller can assign any value
# without any validation.  The object cannot enforce its own invariants.
#
# Flow for  s = SensorRaw("probe", 36.5); s.reading = -9999:
#   1. SensorRaw.__init__ sets self.reading = 36.5  (no checks)
#   2. s.reading = -9999  → Python sets the attribute directly
#      No validation fires — the object silently holds an invalid value.
# ══════════════════════════════════════════════════════════════════════════════

# ── Part 1: Why expose raw attributes is risky ──────────────────────────────

class SensorRaw:
    """No encapsulation — anyone can set anything."""

    def __init__(self, name: str, reading: float):
        self.name = name
        self.reading = reading  # fully public, no protection


def demo_unprotected():
    print("=" * 50)
    print("SECTION 1: No encapsulation — open to invalid state")
    print("=" * 50)

    s = SensorRaw("temperature_probe_1", 36.5)
    print(f"Initial reading: {s.reading}")

    # Nothing stops a caller from setting nonsense
    s.reading = -9999
    print(f"After bad assignment: {s.reading}")
    print("Object is now in an invalid state with no warning.")


# ══════════════════════════════════════════════════════════════════════════════
# PART 2: _ prefix convention — internal by agreement
#
# A single leading underscore is a SIGNAL to other developers:
# "this attribute is internal implementation detail — don't use it directly".
# Python does NOT enforce this; callers can still access _reading directly.
# It's a community convention, not a language barrier.
#
# Flow for  s.set_reading(38.5):
#   1. validate 38.5 >= -273.15 → passes
#   2. self._reading = 38.5  (internal storage updated)
#
# Flow for  s.set_reading(-300):
#   1. validate -300 >= -273.15 → fails
#   2. raise ValueError("Temperature below absolute zero...")
# ══════════════════════════════════════════════════════════════════════════════

# ── Part 2: Encapsulation with naming convention ─────────────────────────────

class SensorEncapsulated:
    """Uses _ prefix to signal that _reading is internal.
    There is no hard enforcement — it's a convention that Python
    respects by convention, not by the runtime.
    """

    def __init__(self, name: str, reading: float):
        self.name = name
        self._reading = reading  # single _ means "internal — don't touch directly"

    def get_reading(self) -> float:
        return self._reading

    def set_reading(self, value: float) -> None:
        if value < -273.15:
            raise ValueError(f"Temperature below absolute zero is not physical: {value}")
        self._reading = value


def demo_convention():
    print("\n" + "=" * 50)
    print("SECTION 2: _ prefix — internal by convention")
    print("=" * 50)

    s = SensorEncapsulated("probe_A", 25.0)
    print(f"Reading via method: {s.get_reading()}")

    s.set_reading(38.5)
    print(f"After set_reading(38.5): {s.get_reading()}")

    try:
        s.set_reading(-300)
    except ValueError as e:
        print(f"Rejected: {e}")

    # You _can_ still bypass it — Python trusts the developer
    s._reading = -300
    print(f"Bypassed via s._reading = -300: {s._reading}")
    print("Convention works, but only by agreement — properties provide real control.")


# ══════════════════════════════════════════════════════════════════════════════
# PART 3: @property — Pythonic validated attribute access
#
# @property makes a method LOOK like a plain attribute to callers.
# The getter is called on read (sensor.reading).
# The setter is called on write (sensor.reading = value).
# Callers use natural attribute syntax; the class enforces invariants silently.
#
# Flow for  s = Sensor("probe", 22.0):
#   1. __init__ sets self.reading = 22.0   (routes through the setter!)
#   2. setter: isinstance(22.0, (int,float))? Yes
#   3.         -273.15 <= 22.0 <= 1000.0?   Yes
#   4.         self._reading = 22.0         (stores the validated float)
#
# Flow for  s.reading = -300:
#   1. setter called with value=-300
#   2. isinstance(-300, (int,float))? Yes
#   3. -273.15 <= -300 <= 1000.0?    No  → raise ValueError
#
# Flow for  s.reading_fahrenheit  (computed property, no setter):
#   1. getter called  → return self._reading * 9/5 + 32
#   2. s.reading_fahrenheit = 100  → AttributeError (no setter defined)
# ══════════════════════════════════════════════════════════════════════════════

# ── Part 3: @property — Pythonic encapsulation ───────────────────────────────

class Sensor:
    """Uses @property for clean, validated attribute access.

    Callers use sensor.reading = value (natural syntax),
    and the setter enforces the invariant automatically.
    """

    MIN_TEMP = -273.15   # Absolute zero in Celsius
    MAX_TEMP = 1_000.0   # Upper sensor limit

    def __init__(self, name: str, reading: float):
        self.name = name
        self.reading = reading  # routes through the setter on __init__ too

    @property
    def reading(self) -> float:
        """Current temperature reading in Celsius."""
        return self._reading

    @reading.setter
    def reading(self, value: float) -> None:
        if not isinstance(value, (int, float)):
            raise TypeError(f"reading must be a number, got {type(value).__name__}")
        if not (self.MIN_TEMP <= value <= self.MAX_TEMP):
            raise ValueError(
                f"reading {value} out of range [{self.MIN_TEMP}, {self.MAX_TEMP}]"
            )
        self._reading = float(value)

    @property
    def reading_fahrenheit(self) -> float:
        """Computed property — derived from the stored Celsius value."""
        return self._reading * 9 / 5 + 32

    def __repr__(self) -> str:
        return f"Sensor(name={self.name!r}, reading={self._reading}°C)"


def demo_property():
    print("\n" + "=" * 50)
    print("SECTION 3: @property — validated, Pythonic access")
    print("=" * 50)

    s = Sensor("probe_B", 22.0)
    print(f"Initial: {s}")
    print(f"In Fahrenheit: {s.reading_fahrenheit:.1f}°F")

    s.reading = 37.5
    print(f"After s.reading = 37.5: {s}")

    # Setter rejects invalid values
    for bad in [-300, 2000, "hot"]:
        try:
            s.reading = bad
        except (ValueError, TypeError) as e:
            print(f"Rejected {bad!r}: {e}")

    # Computed property cannot be set — it has no setter
    try:
        s.reading_fahrenheit = 100
    except AttributeError as e:
        print(f"Can't set computed property: {e}")


def main():
    demo_unprotected()
    demo_convention()
    demo_property()


if __name__ == "__main__":
    main()

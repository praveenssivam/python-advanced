"""
helpers.py
===========
Reusable utility functions and a simple class used by main.py to
demonstrate module imports and the __name__ guard.

This file is meant to be imported, not run directly.
If you run it directly, only the __name__ guard section executes.
"""

from datetime import date


# ── Standalone functions ─────────────────────────────────────────────────────

def format_record(name: str, value: float, unit: str = "units") -> str:
    """Return a formatted string for a named measurement."""
    return f"{name}: {value:.2f} {unit}"


def clamp(value: float, low: float, high: float) -> float:
    """Constrain value to the range [low, high]."""
    return max(low, min(high, value))


def batch_summary(records: list[dict]) -> dict:
    """Summarise a list of {'name': str, 'value': float} records."""
    if not records:
        return {"count": 0, "total": 0.0, "average": None}
    values = [r["value"] for r in records]
    return {
        "count": len(values),
        "total": round(sum(values), 4),
        "average": round(sum(values) / len(values), 4),
    }


# ── A simple class ───────────────────────────────────────────────────────────

class DailyLog:
    """A minimal log of daily measurements."""

    def __init__(self, label: str):
        self.label = label
        self.date = date.today().isoformat()
        self._entries: list[float] = []

    def record(self, value: float) -> None:
        self._entries.append(value)

    def summary(self) -> dict:
        return batch_summary([{"value": v} for v in self._entries])

    def __repr__(self) -> str:
        return f"DailyLog(label={self.label!r}, entries={len(self._entries)})"


# ── Guard ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Running helpers.py directly — just a quick self-check
    print("helpers.py executed directly (not imported).")
    print(format_record("temperature", 36.7, "°C"))
    print(f"clamp(150, 0, 100) = {clamp(150, 0, 100)}")

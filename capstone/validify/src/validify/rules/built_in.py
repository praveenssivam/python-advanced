"""
rules/built_in.py — Concrete validation rules and rule factory.

─────────────────────────────────────────────────────────
DAY 1 TASK
─────────────────────────────────────────────────────────
Implement concrete rules as subclasses of BaseValidator.
Each mirrors a function in starter/validate_trips.py:

  NullCheckRule(field: str)
    — Fails when the field is absent, None, or an empty/whitespace string.
    — Mirror of: check_not_null()

  RangeRule(field: str, min: float, max: float)
    — Fails when the field is not a number or is outside [min, max].
    — Mirror of: check_range()

  CoordinateRule(field: str, min: float, max: float)
    — Fails when a geographic coordinate is outside the bounding box.
    — Mirror of: check_coordinate()
    — Hint: the logic is almost identical to RangeRule — what does this
      tell you about inheritance or composition?

Part B (stretch):
  DateFormatRule(field: str, fmt: str = "%Y-%m-%d %H:%M:%S")
    — Fails when the field cannot be parsed as a datetime in the given format.
    — Mirror of: check_date_format()

Each rule must store self.field and any other config params in __init__.
The 'type' name used in config/rules.yaml is the snake_case class name:
  NullCheckRule  → null_check_rule
  RangeRule      → range_rule
  CoordinateRule → coordinate_rule
  DateFormatRule → date_format_rule

─────────────────────────────────────────────────────────
DAY 3 TASK — add RegexRule and RuleFactory
─────────────────────────────────────────────────────────
  RegexRule(field: str, pattern: str)
    — Fails when the field value does not match re.fullmatch(pattern, value).
    — Mirror of: check_allowed_values() but more general.
    — Needed for the payment_type rule in config/rules.yaml.
    — type name: regex_rule

  RuleFactory:
      @staticmethod
      def from_config(path: str) -> list[BaseValidator]:
          # 1. Open and parse the YAML file.
          # 2. For each entry, look up the class: ValidatorRegistry.get(entry["type"])
          # 3. Instantiate it passing the remaining keys as kwargs.
          # 4. Return the list.

─────────────────────────────────────────────────────────
DAY 5 — Git exercise
─────────────────────────────────────────────────────────
On a feature branch, add RegexRule if not done yet, confirm it is
registered and works via a unit test, then merge back to main.
"""

import re  # noqa: F401 — needed by RegexRule
import yaml  # noqa: F401 — needed by RuleFactory

from validify.core.base import BaseValidator  # noqa: F401
from validify.core.exceptions import ConfigError  # noqa: F401
from validify.rules.registry import ValidatorRegistry  # noqa: F401


# ---------------------------------------------------------------------------
# YOUR CODE BELOW
# ---------------------------------------------------------------------------

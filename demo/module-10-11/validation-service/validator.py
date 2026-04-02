"""Validation module for the validation-service FastAPI application.

This module contains three independent validation functions consumed by the
POST /validate endpoint. Each function receives the full request payload as a
dict and returns a status dict.

Git conflict zone (Module 9 exercise):
  Two feature branches independently modify the error-message return line inside
  validate_input(), which is marked '# ← CONFLICT ZONE':

    feature/add-validator :  changes the message to "Required key missing: {key}"
    feature/update-schema :  changes the message to "Validation error: missing key: {key}"

  After feature/add-validator is merged into main, merging feature/update-schema
  produces a genuine, deterministic conflict — both branches changed the same
  ancestor line to different values, so Git cannot auto-resolve it.
"""

from typing import Any


def validate_input(data: dict[str, Any]) -> dict[str, Any]:
    """Check that both 'name' and 'value' keys are present in the payload.

    Args:
        data: The request payload dictionary.

    Returns:
        {"status": "ok"} when both keys are present.
        {"status": "error", "message": "Missing key: <key>"} on first missing key.
    """
    for key in ("name", "value"):
        if key not in data:
            return {"status": "error", "message": f"Missing key: {key}"}  # ← CONFLICT ZONE
    return {"status": "ok"}


def validate_schema(data: dict[str, Any]) -> dict[str, Any]:
    """Check that 'value' is present, is a non-bool integer, and is positive.

    Args:
        data: The request payload dictionary.

    Returns:
        {"status": "ok"} on success.
        {"status": "error", "message": "<reason>"} on failure.
    """
    if "value" not in data:
        return {"status": "error", "message": "Missing key: value"}

    value = data["value"]

    # bool is a subclass of int in Python — isinstance(True, int) is True.
    # Exclude booleans explicitly so they are not accepted as valid integers.
    if not isinstance(value, int) or isinstance(value, bool):
        return {"status": "error", "message": "value must be an integer"}

    if value <= 0:
        return {"status": "error", "message": "value must be a positive integer"}

    return {"status": "ok"}


def validate_category(data: dict[str, Any]) -> dict[str, Any]:
    """Check the optional 'category' field when it is present.

    'category' is not required. If absent, this validator returns ok immediately.
    If present, it must be a non-empty, non-whitespace-only string.

    Args:
        data: The request payload dictionary.

    Returns:
        {"status": "ok"} when absent or valid.
        {"status": "error", "message": "<reason>"} when present but invalid.
    """
    if "category" not in data:
        return {"status": "ok"}

    category = data["category"]

    if not isinstance(category, str):
        return {"status": "error", "message": "category must be a non-empty string"}

    if not category.strip():
        return {"status": "error", "message": "category must be a non-empty string"}

    return {"status": "ok"}

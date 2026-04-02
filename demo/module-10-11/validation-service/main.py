"""FastAPI application for the validation-service.

Endpoints:
  GET  /         → service identity and version
  GET  /health   → health check used by Docker HEALTHCHECK and orchestrators
  POST /validate → runs all three validators and collects every error before responding
"""

from typing import Any

from fastapi import Body, FastAPI, HTTPException

from validator import validate_category, validate_input, validate_schema

app = FastAPI(title="Validation Service", version="1.0.0")


@app.get("/")
async def root() -> dict[str, str]:
    """Return service identity and version."""
    return {"service": "validation-service", "version": "1.0.0", "status": "running"}


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint.

    Used by the Docker HEALTHCHECK instruction and external orchestrators to
    determine whether the container is ready to serve traffic.
    """
    return {"status": "healthy", "version": "1.0.0"}


@app.post("/validate")
async def validate(data: dict[str, Any] = Body(...)) -> dict[str, Any]:
    """Validate a JSON payload against all three validators.

    All validators run regardless of earlier failures — every error is
    collected before a response is returned. This lets callers fix all
    problems in one round-trip rather than discovering them one at a time.

    Args:
        data: Raw JSON object from the request body.

    Returns:
        {"status": "valid", "data": <payload>} on success.

    Raises:
        HTTPException 422: list of all validation error messages.
    """
    validators = [validate_input, validate_schema, validate_category]
    errors: list[str] = []

    for validator in validators:
        result = validator(data)
        if result["status"] == "error":
            errors.append(result["message"])

    if errors:
        raise HTTPException(status_code=422, detail=errors)

    return {"status": "valid", "data": data}

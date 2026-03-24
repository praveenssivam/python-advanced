"""
api/app.py — FastAPI application with three routes.

─────────────────────────────────────────────────────────
DAY 4 TASK
─────────────────────────────────────────────────────────
Implement a minimal FastAPI application with these three routes:

  GET  /health
    Returns: {"status": "ok", "version": "0.1.0"}

  POST /validate
    Accepts:  UploadFile (a CSV file)
    Process:
      1. Read the uploaded file bytes and decode to a string.
      2. Parse as CSV using csv.DictReader(io.StringIO(content)).
      3. Load rules from config/rules.yaml.
      4. Run validation using your engine from runner.py.
      5. Build a Report from the results.
      6. Store the Report in the module-level REPORTS dict keyed by a run_id.
      7. Return: {"run_id": "<uuid>", "summary": {"total": N, "passed": N, ...}}

  GET  /reports/{run_id}
    Returns the stored Report as JSON.
    Returns HTTP 404 if run_id is not found.

─────────────────────────────────────────────────────────
TIPS
─────────────────────────────────────────────────────────
  - Use uuid.uuid4() to generate run IDs.
  - Store reports in a module-level dict (not a database).
  - Run with: uvicorn validify.api.app:app --reload
  - The config file is at config/rules.yaml relative to the project root.
    Pass its path as an argument or use an environment variable.
"""

import csv
import io
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile  # noqa: F401

# Add your own imports from validify modules as needed.

# In-memory report store: {run_id: Report}
REPORTS: dict = {}


def create_app() -> FastAPI:
    app = FastAPI(
        title="Validify",
        version="0.1.0",
        description="Enterprise Data Validation & Processing Service",
    )

    # ---------------------------------------------------------------------------
    # YOUR ROUTES BELOW
    # ---------------------------------------------------------------------------

    return app


app = create_app()

# Validation Service

A FastAPI-based data validation service used as the hands-on training project for the Python Advanced course.

## What This Project Is

This repository is the carry-forward project used across three consecutive modules of the Python Advanced course:

- **Module 9 — Git**: Initialize the repo, practice branching, simulate and resolve a merge conflict, tag a release.
- **Module 10 — Docker**: Containerize the service with a simple single-stage build, then optimize with a multi-stage build.
- **Module 11 — CI/CD**: Automate lint, test, and Docker build with a GitHub Actions pipeline.

The repository is treated as a real project from Module 9 onward. Changes from each module carry forward into the next.

---

## Project Structure

```
validation-service/
├── main.py                    # FastAPI application — three endpoints
├── validator.py               # Three validator functions (conflict zone for Module 9)
├── tests/
│   ├── __init__.py            # Makes tests/ a Python package
│   └── test_validator.py      # Unit tests for all three validators
├── requirements.txt           # Pinned dependencies: fastapi, uvicorn, pytest, ruff
├── .gitignore                 # Python, env, IDE, and OS exclusions
├── .dockerignore              # Excludes tests, docs, and build files from the image
├── Dockerfile                 # Simple single-stage build (Module 10 Step 1)
├── Dockerfile.multistage      # Multi-stage lean build (Module 10 Step 2)
├── .github/
│   └── workflows/
│       └── ci.yml             # GitHub Actions: Lint → Test → Build
└── README.md                  # This file
```

---

## Getting Started

### Prerequisites

- Python 3.11+, pip, virtualenv
- Docker Desktop
- Git 2.30+

### Run Locally

```bash
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Open http://localhost:8000 in your browser or use `curl`.

### Run Tests

```bash
pytest tests/ -v
```

### Run with Docker (Simple)

```bash
docker build -t validation-service:simple .
docker run -p 8000:8000 validation-service:simple
```

### Run with Docker (Multi-Stage)

```bash
docker build -f Dockerfile.multistage -t validation-service:lean .
docker run -p 8000:8000 validation-service:lean
docker image ls validation-service   # compare sizes
```

---

## API Endpoints

| Method | Path | Description | Example Response |
|--------|------|-------------|-----------------|
| GET | `/` | Service identity and version | `{"service": "validation-service", "version": "1.0.0", "status": "running"}` |
| GET | `/health` | Health check for Docker and orchestrators | `{"status": "healthy", "version": "1.0.0"}` |
| POST | `/validate` | Validate a JSON payload — all errors collected before responding | `{"status": "valid", "data": {...}}` or HTTP 422 with list of errors |

**Example valid request:**

```bash
curl -X POST http://localhost:8000/validate \
  -H "Content-Type: application/json" \
  -d '{"name": "test", "value": 42, "category": "premium"}'
```

**Example error response (HTTP 422):**

```json
{
  "detail": [
    "Missing key: name",
    "value must be a positive integer"
  ]
}
```

---

## CI Pipeline

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every push and pull request to `main`.

Pipeline stages in order:

| Step | Action | Why here |
|------|--------|----------|
| Checkout | `actions/checkout@v4` | Fetch source code — must be first |
| Set up Python 3.11 | `actions/setup-python@v5` | Install runtime before pip |
| Cache pip | `actions/cache@v4` | Reuse downloaded wheels — saves ~30 s |
| Install dependencies | `pip install -r requirements.txt` | After cache restore |
| Lint | `ruff check .` | Fast feedback before running tests |
| Test | `pytest tests/ --tb=short -q` | Must pass before building |
| Build Docker image | `docker build` | Only runs on green lint + tests |

The Docker image is tagged with the commit SHA (`github.sha`) so every build is uniquely traceable to its source commit.

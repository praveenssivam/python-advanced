"""
12_fastapi_async_api.py
========================
FastAPI + asyncio: concurrent validation API.

This file bridges the asyncio patterns from file 10 to a real HTTP server.
It is the reference implementation for the Module 6 capstone upgrade.

Architecture:
  POST /validate        → validate one record (3 rules concurrently)
  POST /validate-batch  → validate many records (all run concurrently)
  GET  /health          → liveness check

Key patterns shown:
  - Pydantic request/response models (input validation for free)
  - async route handlers — each request is a coroutine
  - asyncio.gather() inside a route — rules run concurrently per request
  - asyncio.Semaphore — cap concurrency when calling external APIs
  - asyncio.wait_for() — timeout guard per request
  - lifespan context manager — startup/shutdown resource management
  - HTTPException for expected error responses

Run (self-contained — starts uvicorn programmatically):
    python demo/module-06/12_fastapi_async_api.py

Test with curl (in a second terminal while server is running):
    curl -s -X POST http://localhost:8000/validate \
         -H "Content-Type: application/json" \
         -d '{"id": 1, "email": "alice@example.com", "name": "Alice Smith", "age": 30}' | python -m json.tool

    curl -s -X POST http://localhost:8000/validate-batch \
         -H "Content-Type: application/json" \
         -d '[{"id":1,"email":"alice@example.com","name":"Alice Smith","age":30},
              {"id":2,"email":"bob-invalid","name":"Bob","age":25},
              {"id":3,"email":"carol@corp.io","name":"Carol 123!","age":40}]' | python -m json.tool

Or use the built-in benchmark (runs automatically when script starts):
    python demo/module-06/12_fastapi_async_api.py --bench
"""

import asyncio
import re
import time
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, field_validator


# ══════════════════════════════════════════════════════════════════════════════
# Pydantic models — FastAPI uses these for automatic request validation
# and OpenAPI schema generation (docs at http://localhost:8000/docs)
# ══════════════════════════════════════════════════════════════════════════════

class RecordIn(BaseModel):
    id: int
    email: str
    name: str
    age: int


class RuleResult(BaseModel):
    rule: str
    passed: bool
    message: str = ""
    elapsed_ms: float


class ValidationResponse(BaseModel):
    record_id: int
    passed: bool
    rules: list[RuleResult]
    total_elapsed_ms: float


class BatchResponse(BaseModel):
    total: int
    passed: int
    failed: int
    results: list[ValidationResponse]
    wall_elapsed_ms: float


# ══════════════════════════════════════════════════════════════════════════════
# Async validation rules
#
# Each rule is a plain async function — easy to test, easy to swap.
# In production these would await DB, cache, or external API calls.
# Here they simulate that latency with asyncio.sleep().
# ══════════════════════════════════════════════════════════════════════════════

async def rule_email(record: RecordIn) -> RuleResult:
    """Simulate async DNS/uniqueness check (100ms)."""
    t0 = time.perf_counter()
    await asyncio.sleep(0.10)   # production: await db.fetchrow(...)
    passed = "@" in record.email and "." in record.email.split("@")[-1]
    return RuleResult(
        rule="email",
        passed=passed,
        message="" if passed else f"invalid email: {record.email!r}",
        elapsed_ms=round((time.perf_counter() - t0) * 1000, 1),
    )


async def rule_name_length(record: RecordIn) -> RuleResult:
    """Simulate async config fetch for length limits (50ms)."""
    t0 = time.perf_counter()
    await asyncio.sleep(0.05)   # production: await cache.get("cfg:name_limits")
    passed = 2 <= len(record.name) <= 100
    return RuleResult(
        rule="name_length",
        passed=passed,
        message="" if passed else f"name length {len(record.name)} not in [2, 100]",
        elapsed_ms=round((time.perf_counter() - t0) * 1000, 1),
    )


_NAME_PATTERN = re.compile(r"^[A-Za-z ,.'\-]{2,100}$")

async def rule_name_format(record: RecordIn) -> RuleResult:
    """Simulate async regex pattern registry fetch (80ms)."""
    t0 = time.perf_counter()
    await asyncio.sleep(0.08)   # production: await rules_db.fetchrow(...)
    passed = bool(_NAME_PATTERN.match(record.name))
    return RuleResult(
        rule="name_format",
        passed=passed,
        message="" if passed else f"name has invalid characters: {record.name!r}",
        elapsed_ms=round((time.perf_counter() - t0) * 1000, 1),
    )


# All rules as a list — easy to extend
ALL_RULES = [rule_email, rule_name_length, rule_name_format]


# ══════════════════════════════════════════════════════════════════════════════
# Core validation logic — used by both route handlers
#
# asyncio.gather(..., return_exceptions=True):
#   Runs all rules concurrently. If one raises an exception, the others
#   still complete and we handle the error per-rule (not abort everything).
#
# asyncio.wait_for(..., timeout=5.0):
#   Guards against slow external calls hanging the server indefinitely.
# ══════════════════════════════════════════════════════════════════════════════

async def validate_record(record: RecordIn) -> ValidationResponse:
    t0 = time.perf_counter()

    # Run all rules concurrently — total ≈ max(rule latencies) not sum
    raw = await asyncio.wait_for(
        asyncio.gather(*[rule(record) for rule in ALL_RULES], return_exceptions=True),
        timeout=5.0,
    )

    rule_results: list[RuleResult] = []
    for i, r in enumerate(raw):
        if isinstance(r, Exception):
            rule_results.append(RuleResult(
                rule=f"rule_{i}", passed=False,
                message=f"rule raised: {r}",
                elapsed_ms=0.0,
            ))
        else:
            rule_results.append(r)

    return ValidationResponse(
        record_id=record.id,
        passed=all(r.passed for r in rule_results),
        rules=rule_results,
        total_elapsed_ms=round((time.perf_counter() - t0) * 1000, 1),
    )


# ══════════════════════════════════════════════════════════════════════════════
# Semaphore — rate limiting for batch requests
#
# Without this, a batch of 1000 records would fire 3000 simultaneous
# "DB queries". A Semaphore(10) means at most 10 records are validated
# at a time — keeps pressure on downstream services manageable.
# ══════════════════════════════════════════════════════════════════════════════

_batch_semaphore = asyncio.Semaphore(10)   # max 10 concurrent validations


async def validate_record_limited(record: RecordIn) -> ValidationResponse:
    async with _batch_semaphore:
        return await validate_record(record)


# ══════════════════════════════════════════════════════════════════════════════
# Lifespan — startup / shutdown resource management
#
# The recommended pattern in FastAPI >= 0.93 (replaces @app.on_event).
# Use this to open DB connection pools, load ML models, warm caches.
# Resources created here are available for the entire server lifetime.
# ══════════════════════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── startup ──────────────────────────────────────────────────────────────
    print("  [lifespan] server starting — warming up rule registry...")
    await asyncio.sleep(0.01)   # production: await db_pool.open() etc.
    print("  [lifespan] ready.")
    yield
    # ── shutdown ─────────────────────────────────────────────────────────────
    print("  [lifespan] server shutting down — closing connections.")
    await asyncio.sleep(0.01)   # production: await db_pool.close() etc.


# ══════════════════════════════════════════════════════════════════════════════
# FastAPI app + routes
# ══════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="Async Validation API",
    description="Module 6 demo — asyncio + FastAPI concurrent validation service",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> dict:
    """Liveness probe — always returns 200 OK."""
    return {"status": "ok"}


@app.post("/validate", response_model=ValidationResponse)
async def validate_one(record: RecordIn) -> ValidationResponse:
    """
    Validate a single record against all rules concurrently.

    Rules run in parallel — total latency ≈ slowest rule (100ms),
    not the sum of all rules (230ms).
    """
    try:
        return await validate_record(record)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="validation timed out")


@app.post("/validate-batch", response_model=BatchResponse)
async def validate_batch(records: list[RecordIn]) -> BatchResponse:
    """
    Validate a list of records — all processed concurrently.

    A Semaphore(10) limits concurrent validations to avoid overloading
    downstream services (DB / cache), while still processing the batch
    much faster than sequential validation would.
    """
    if not records:
        raise HTTPException(status_code=422, detail="records list must not be empty")
    if len(records) > 500:
        raise HTTPException(status_code=422, detail="batch size must not exceed 500")

    t0 = time.perf_counter()

    results = await asyncio.gather(
        *[validate_record_limited(r) for r in records],
        return_exceptions=True,
    )

    final: list[ValidationResponse] = []
    for i, res in enumerate(results):
        if isinstance(res, Exception):
            # One record's failure must not abort the entire batch
            final.append(ValidationResponse(
                record_id=records[i].id,
                passed=False,
                rules=[RuleResult(rule="error", passed=False, message=str(res), elapsed_ms=0.0)],
                total_elapsed_ms=0.0,
            ))
        else:
            final.append(res)

    passed = sum(1 for r in final if r.passed)
    return BatchResponse(
        total=len(final),
        passed=passed,
        failed=len(final) - passed,
        results=final,
        wall_elapsed_ms=round((time.perf_counter() - t0) * 1000, 1),
    )


# ══════════════════════════════════════════════════════════════════════════════
# Built-in benchmark — runs without a live server, using httpx's async client
#
# Demonstrates the performance claim from the slide:
#   Sequential: 3 × 100ms = 300ms
#   Concurrent: ~100ms (one event loop, all three run in parallel)
# ══════════════════════════════════════════════════════════════════════════════

async def run_benchmark():
    """
    Direct benchmark — calls validate_record() without HTTP overhead.
    Shows the concurrency gain without needing a running server.
    """
    records = [
        RecordIn(id=1, email="alice@example.com", name="Alice Smith",  age=30),
        RecordIn(id=2, email="bob-invalid",        name="Bob",          age=25),
        RecordIn(id=3, email="carol@corp.io",       name="Carol 123!",  age=40),
        RecordIn(id=4, email="dan@test.org",        name="Dan",         age=28),
        RecordIn(id=5, email="eve@domain.net",      name="Eve Johnson", age=35),
        RecordIn(id=6, email="frank@example.com",   name="Frank",       age=22),
        RecordIn(id=7, email="grace@corp.net",      name="Grace-Lee",   age=45),
        RecordIn(id=8, email="henry@web.io",        name="Henry Brown", age=33),
        RecordIn(id=9, email="iris@invalid",        name="Iris",        age=29),
        RecordIn(id=10, email="jack@example.org",   name="Jack Smith",  age=50),
    ]

    print("=" * 60)
    print("BENCHMARK 1: Sequential — one record at a time")
    print("=" * 60)
    t0 = time.perf_counter()
    for r in records:
        res = await validate_record(r)
    seq_elapsed = time.perf_counter() - t0
    print(f"  10 records × ~{seq_elapsed/10*1000:.0f}ms = {seq_elapsed*1000:.0f}ms total")

    print()
    print("=" * 60)
    print("BENCHMARK 2: Concurrent — all 10 records simultaneously")
    print("=" * 60)
    t0 = time.perf_counter()
    results = await asyncio.gather(*[validate_record(r) for r in records])
    conc_elapsed = time.perf_counter() - t0

    for res in results:
        status = "✓ PASS" if res.passed else "✗ FAIL"
        rule_line = "  ".join(f"{r.rule}={r.elapsed_ms:.0f}ms" for r in res.rules)
        print(f"  record {res.record_id:>2}: {status}  [{rule_line}]  total={res.total_elapsed_ms:.0f}ms")

    print(f"\n  10 records gathered: {conc_elapsed*1000:.0f}ms total")
    print(f"  Speedup: {seq_elapsed/conc_elapsed:.1f}× faster than sequential")

    print()
    print("=" * 60)
    print("BENCHMARK 3: FastAPI route handlers are coroutines too")
    print("=" * 60)
    print()
    print("  When uvicorn receives 10 simultaneous HTTP requests, each request")
    print("  triggers an async route handler. All 10 run concurrently on the")
    print("  SAME thread — no threads, no GIL, no multiprocessing.")
    print()
    print("  Sync Flask (3 clients, 100ms each):")
    print("    Client 1 ──► [████ 100ms ████]")
    print("    Client 2 ──────────────────────► [████ 100ms ████]")
    print("    Client 3 ──────────────────────────────────────────► [████ 100ms ████]")
    print("    Wall time: 300ms")
    print()
    print("  Async FastAPI (3 clients, 100ms each):")
    print("    Client 1 ──► [████ 100ms ████]")
    print("    Client 2 ──► [████ 100ms ████]  ← concurrent")
    print("    Client 3 ──► [████ 100ms ████]")
    print("    Wall time: ~100ms  ✓")
    print()
    print("  Run the server (python demo/module-06/12_fastapi_async_api.py)")
    print("  and browse to http://localhost:8000/docs for the interactive UI.")


# ══════════════════════════════════════════════════════════════════════════════
# Entry point
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    if "--bench" in sys.argv or len(sys.argv) == 1:
        # Default: run the benchmark first, then start the server
        print()
        print("Running benchmark (no HTTP server needed)...")
        print()
        asyncio.run(run_benchmark())
        print()

    if "--bench" not in sys.argv or "--serve" in sys.argv:
        print("Starting FastAPI server on http://localhost:8000")
        print("  Docs:    http://localhost:8000/docs")
        print("  Redoc:   http://localhost:8000/redoc")
        print("  Press Ctrl+C to stop.")
        print()
        uvicorn.run(
            "12_fastapi_async_api:app",
            host="127.0.0.1",
            port=8000,
            reload=False,
            log_level="warning",   # suppress per-request noise in demo
        )

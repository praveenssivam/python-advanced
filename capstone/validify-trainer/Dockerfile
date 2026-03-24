# --- Stage 1: builder ---
# Install dependencies and build the wheel.
FROM python:3.12-slim AS builder

WORKDIR /build

COPY pyproject.toml .
COPY src/ src/

RUN pip install --no-cache-dir hatchling \
    && pip install --no-cache-dir .

# ---------------------------------------------------------------------------
# TODO (Day 5):
#   The above installs into the system Python inside the builder stage.
#   For multi-stage builds, typically you would:
#     1. Install into a prefix: pip install --prefix=/install .
#     2. Copy /install into the runtime stage.
#   For simplicity in training, a single-stage approach is also acceptable.
# ---------------------------------------------------------------------------


# --- Stage 2: runtime ---
# Copy only what is needed. Run as non-root.
FROM python:3.12-slim AS runtime

WORKDIR /app

# TODO (Day 5 — complete these lines):
#
# 1. Copy installed packages from builder:
#    COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
#    COPY --from=builder /usr/local/bin/uvicorn /usr/local/bin/uvicorn
#
# 2. Copy application source:
#    COPY src/ src/
#    COPY config/ config/
#
# 3. Create a non-root user and switch to it:
#    RUN useradd -m appuser
#    USER appuser
#
# 4. Expose the port and set the startup command:
#    EXPOSE 8000
#    CMD ["uvicorn", "validify.api.app:app", "--host", "0.0.0.0", "--port", "8000"]

EXPOSE 8000

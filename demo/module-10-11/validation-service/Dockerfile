# =============================================================================
# Simple Single-Stage Build — Module 10 Step 1
# =============================================================================
# Build:   docker build -t validation-service:simple .
# Run:     docker run -p 8000:8000 validation-service:simple
# Verify:  curl http://localhost:8000/health
#
# After also building Dockerfile.multistage, compare sizes with:
#   docker image ls validation-service
# =============================================================================

# Use the full Python 3.11 base image.
# The "full" image includes build tools (gcc, pip headers, etc.) which makes
# it convenient for a first build — pip can compile any C extensions without
# extra setup. The trade-off is a large final image (~900 MB).
# We address this in Dockerfile.multistage using the slim variant.
FROM python:3.11

# Set the working directory inside the container.
# All subsequent COPY, RUN, and CMD instructions resolve paths relative to /app.
# The directory is created automatically if it does not exist.
WORKDIR /app

# LAYER CACHING TRICK — copy requirements.txt BEFORE copying the rest of the app.
#
# Docker caches each instruction as a layer and only rebuilds layers whose
# inputs have changed. requirements.txt changes far less often than .py files.
# By copying it first and running pip install before COPY . ., Docker can
# reuse the cached pip install layer on every build where only your source
# code changed — saving 30–60 seconds per rebuild.
#
# If you did COPY . . first, every code change would invalidate the pip layer
# and force a full re-install of all packages, even though nothing in
# requirements.txt changed.
COPY requirements.txt .

# Install all Python dependencies declared in requirements.txt.
# --no-cache-dir prevents pip from writing its download cache to disk inside
# the image layer, keeping the image a few MB smaller.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application source code into /app.
# This happens AFTER pip install so that editing .py files does not invalidate
# the dependency installation layer (see LAYER CACHING TRICK above).
# Files listed in .dockerignore (tests/, *.md, .git/, etc.) are excluded.
COPY . .

# Declare the port the application will listen on at runtime.
# EXPOSE is metadata — it documents intent but does NOT publish the port.
# To actually reach the container, use `docker run -p 8000:8000 ...` which
# maps container port 8000 to a port on your host machine.
EXPOSE 8000

# Health check so Docker knows when the container is live and healthy.
# Uses Python's built-in urllib — no need to install curl as an extra dependency.
#
# --interval=30s    run the check every 30 seconds after the container starts
# --timeout=5s      a check that takes longer than 5 s is counted as failed
# --start-period=15s give the application 15 s to initialise before checks begin
# --retries=3       mark the container "unhealthy" after 3 consecutive failures
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Default command: start the FastAPI application with uvicorn.
# Using JSON array form (exec form) so signals (SIGTERM) go directly to uvicorn,
# not to a shell — this enables graceful shutdown.
#
# --host 0.0.0.0   listen on all network interfaces inside the container.
#                  Without this, uvicorn binds to 127.0.0.1 only, which is
#                  not reachable from outside the container.
# --port 8000      must match the port declared in EXPOSE above.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

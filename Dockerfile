# ── Stage 1: Builder ──────────────────────────────────────────────────────────
FROM python:3.12-slim-bookworm AS builder

WORKDIR /app

# Install build deps (none currently, but layer is cached)
RUN apt-get update && apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
# Install runtime deps only (no dev extras)
RUN pip install --no-cache-dir . 2>/dev/null || \
    pip install --no-cache-dir fastmcp asyncpg pydantic-settings

COPY src/ ./src/

# ── Stage 2: Runtime ─────────────────────────────────────────────────────────
FROM python:3.12-slim-bookworm

WORKDIR /app

# Copy installed packages and application code from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app/src ./src

# FastMCP defaults to port 8000 for streamable-http
EXPOSE 8000

# Run the MCP server
CMD ["python", "-m", "src.server"]

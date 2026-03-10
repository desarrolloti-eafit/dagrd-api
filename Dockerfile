# ──────────────────────────────────────────────────────────────────────────────
# Stage 1 – Builder
# Install dependencies in a clean layer so they are cached separately from code.
# ──────────────────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /install

# Install build tools needed only for compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install/packages -r requirements.txt

# ──────────────────────────────────────────────────────────────────────────────
# Stage 2 – Runtime
# Lean final image – only the installed packages and application code.
# ──────────────────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/packages/bin:$PATH" \
    PYTHONPATH="/app/packages/lib/python3.12/site-packages"

WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /install/packages /app/packages

# Copy application source
COPY ./app ./app

# Non-root user for security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

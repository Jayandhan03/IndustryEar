# ── Build stage ───────────────────────────────────────────────────
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt


# ── Runtime stage ─────────────────────────────────────────────────
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

# Non-root user for Cloud Run security best practice
RUN adduser --disabled-password --gecos "" appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source only
COPY app/ ./app/

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8080

# Cloud Run injects $PORT (default 8080); --workers 1 is correct since
# Cloud Run scales by spawning more containers, not more in-process workers.
CMD exec uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1

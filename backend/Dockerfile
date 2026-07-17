# ==============================================================================
# Stage 1: Build Python Virtual Environment & Wheels
# ==============================================================================
FROM python:3.13-slim AS builder

WORKDIR /build

# Install compiler utilities required for PostgreSQL database drivers
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --upgrade pip

COPY requirements.txt .

# Construct isolated virtual environment and compile dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt


# ==============================================================================
# Stage 2: Minimal Production Container Runner
# ==============================================================================
FROM python:3.13-slim AS runner

WORKDIR /app

# Install runtime database dynamic libraries required by psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Retrieve pre-compiled virtual environment
COPY --from=builder /opt/venv /opt/venv

# Configure system PATH to prioritize virtual environment binaries
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy application source code into runner directory
COPY . .

# Security Hardening: Enforce non-root execution permissions (UID 10001)
RUN useradd --uid 10001 --create-home appuser && \
    chown -R appuser:appuser /app

# Switch executing context to the hardened non-root user
USER appuser

EXPOSE 8000

# Boot ASGI app utilizing Gunicorn process configurations
CMD ["gunicorn", "-c", "gunicorn_conf.py", "app.main:app"]

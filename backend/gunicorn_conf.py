import multiprocessing
import os

# ==============================================================================
# Gunicorn Configuration File for Production FastAPI Deployments
# ==============================================================================

# 1. Binds Gunicorn to all interfaces on port 8000
bind = os.getenv("BIND", "0.0.0.0:8000")

# 2. Worker Processes Allocation
# Calculates workers dynamically based on CPU core counts to prevent thread starvation.
workers_per_core = float(os.getenv("WORKERS_PER_CORE", "1"))
cores = multiprocessing.cpu_count()
default_web_concurrency = int(cores * workers_per_core)
workers = int(os.getenv("WEB_CONCURRENCY", str(default_web_concurrency)))
if workers <= 0:
    workers = 1

# Enforce Uvicorn's worker process for ASGI application handling
worker_class = "uvicorn.workers.UvicornWorker"

# 3. Connection Limits and Lifecycles
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "120"))
timeout = int(os.getenv("GUNICORN_TIMEOUT", "120"))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "120"))

# 4. Standardized Logging Channels
# Sends access and error logs directly to stdout/stderr for container logs collection (e.g. Loki, Datadog)
loglevel = os.getenv("LOG_LEVEL", "info")
accesslog = os.getenv("ACCESS_LOG", "-")
errorlog = os.getenv("ERROR_LOG", "-")

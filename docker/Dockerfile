# Multi-stage build for production Flask application
# Stage 1: Builder
FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY website/requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt \
    && pip install --user --no-cache-dir \
    gunicorn==21.2.0 \
    psycopg2-binary==2.9.9 \
    python-dotenv==1.0.0 \
    Flask-Migrate==4.0.5

# Stage 2: Runtime
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/home/appuser/.local/bin:$PATH \
    FLASK_APP=app.py \
    FLASK_ENV=production

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# Copy application code - create website module structure
COPY --chown=appuser:appuser website/ /app/website/

# Copy database migrations
COPY --chown=appuser:appuser website/migrations/ /app/website/migrations/

# Copy app.py to /app root
COPY --chown=appuser:appuser website/app.py /app/app.py

# Copy project directories to root level (app.py expects them at parent directory)
COPY --chown=appuser:appuser AI_Development/ /AI_Development/
COPY --chown=appuser:appuser Health_and_Fitness/ /Health_and_Fitness/

# Copy Docker entrypoint script
COPY --chown=appuser:appuser docker/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Create directories for logs and uploads
RUN mkdir -p logs uploads website/static/uploads && \
    chown -R appuser:appuser logs uploads website && \
    find website/static -type f -exec chmod 644 {} \; 2>/dev/null || true && \
    find website/static -type d -exec chmod 755 {} \; 2>/dev/null || true

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=5 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Expose port
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# Run with gunicorn (4 workers as specified)
CMD ["gunicorn", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--worker-class", "sync", \
     "--worker-tmp-dir", "/dev/shm", \
     "--access-logfile", "logs/access.log", \
     "--error-logfile", "logs/error.log", \
     "--log-level", "info", \
     "app:app"]

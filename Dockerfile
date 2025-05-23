# Build stage
FROM python:3.8-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy core package and install it
COPY core /app/core
RUN pip install --no-cache-dir -e /app/core

# Copy management API requirements and build wheels
COPY management_api/requirements.txt /app/management_api/
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r /app/management_api/requirements.txt

# Final stage
FROM python:3.8-slim

WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 appuser

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels and install dependencies
COPY --from=builder /app/wheels /app/wheels
COPY --from=builder /app/core /app/core

# Copy the entire management_api directory
COPY management_api /app/management_api

# Install packages
RUN pip install --no-cache-dir /app/wheels/* && \
    pip install -e /app/core && \
    cd /app/management_api && pip install -e .

# Set Python path
ENV PYTHONPATH=/app/core/src:/app/management_api/src
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set permissions
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Run the application
WORKDIR /app/management_api/src
CMD ["python", "-m", "uvicorn", "opmas_mgmt_api.main:app", "--host", "0.0.0.0", "--port", "8000"] 
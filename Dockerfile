# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies for matplotlib and osmnx
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgeos-dev \
    libproj-dev \
    libgdal-dev \
    fonts-roboto \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p posters cache fonts templates themes

# Set environment variables
ENV FLASK_APP=web_ui.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV CACHE_DIR=/app/cache

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Run with gunicorn for production
# Workers: 2-4 per CPU core
# Threads: 4 per worker for I/O-bound tasks (network requests to OSM)
# Timeout: 300s for large map generation
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--threads", "4", "--timeout", "300", "--worker-class", "gthread", "web_ui:app"]

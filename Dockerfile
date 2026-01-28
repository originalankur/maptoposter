# Multi-stage build for Map Poster Generator

# Stage 1: Build frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app/webapp

# Copy frontend package files
COPY webapp/package*.json ./

# Install dependencies
RUN npm ci

# Copy frontend source
COPY webapp/ ./

# Build frontend
RUN npm run build

# Stage 2: Python backend with built frontend
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies for matplotlib and osmnx
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libgeos-dev \
    libgeos++-dev \
    gdal-bin \
    libgdal-dev \
    libspatialindex-dev \
    fontconfig \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster Python package management
RUN pip install --no-cache-dir uv

# Copy Python dependency files
COPY pyproject.toml requirements.txt ./

# Install Python dependencies using uv
RUN uv pip install --system -r requirements.txt

# Copy application source
COPY create_map_poster.py ./
COPY font_management.py ./
COPY api_server.py ./

# Copy fonts and themes
COPY fonts/ ./fonts/
COPY themes/ ./themes/

# Copy built frontend from stage 1
COPY --from=frontend-builder /app/webapp/dist ./webapp/dist

# Create posters directory
RUN mkdir -p posters

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/').raise_for_status()" || exit 1

# Run the application
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]

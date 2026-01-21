FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required by geopandas/osmnx
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libspatialindex-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy everything (.dockerignore excludes posters, cache, git, etc.)
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create excluded directories for use in docker-only context
RUN mkdir -p posters cache
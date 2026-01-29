# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Install system dependencies required for geospatial libraries
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    libspatialindex-dev \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for GDAL
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY create_map_poster.py .
COPY font_management.py .
COPY themes/ themes/
COPY fonts/ fonts/

# Create directories for output and cache
RUN mkdir -p posters cache

# Set the entrypoint to run the Python script
ENTRYPOINT ["python", "create_map_poster.py"]

# Default command (can be overridden)
CMD ["--help"]

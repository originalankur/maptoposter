FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for matplotlib and osmnx
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY create_map_poster.py .
COPY themes/ themes/
COPY fonts/ fonts/

# Create output directory
RUN mkdir -p posters

# Set default command (can be overridden)
ENTRYPOINT ["python", "create_map_poster.py"]
CMD ["--help"]
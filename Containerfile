# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Install system dependencies for geopandas, pyproj, osmnx, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
	build-essential \
	python3-dev \
	python3-pip \
	fonts-dejavu-core \
	&& rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and resources
COPY create_map_poster.py ./
COPY fonts ./fonts
COPY themes ./themes

# Create posters output directory
RUN mkdir -p posters

# Default command
ENTRYPOINT ["python", "create_map_poster.py"]

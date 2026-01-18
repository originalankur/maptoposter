FROM python:3.11-slim

# Install system dependencies for geospatial libraries
RUN apt-get update && apt-get install -y \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy application files
COPY . .

# Render uses PORT env variable
ENV PORT=10000
EXPOSE $PORT

# Run with gunicorn (using shell form to expand $PORT)
CMD gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120

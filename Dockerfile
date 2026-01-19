# --- STAGE 1 : BUILDER (Compilation) ---
FROM python:3.11-slim as builder

# 1. Build tools
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    libspatialindex-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Isolated virtualenv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 3. Ultra-light clone (without history)
RUN git clone --depth 1 https://github.com/cthonney/maptoposter-docker.git .

# 4. Install deps (Works well with Py 3.11)
RUN pip install --no-cache-dir -r requirements.txt


# --- STAGE 2 : RUNTIME (Production) ---
FROM python:3.11-slim

# 1. System lib required for OSMnx/Rtree
# Using the -dev version which is stable on Debian Bookworm (base of python:3.11)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libspatialindex-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Copy venv and code from stage 1
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app /app

# 3. Security cleanup
RUN rm -rf /app/.git

# 4. Config
ENV PATH="/opt/venv/bin:$PATH"
ENV MPLBACKEND=Agg

EXPOSE 5025

CMD ["python", "app.py"]
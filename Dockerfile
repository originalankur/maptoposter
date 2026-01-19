# --- STAGE 1 : BUILDER (Compilation) ---
FROM python:3.11-slim as builder

# 1. Outils de build
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    libspatialindex-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Virtualenv isolé
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 3. Clone ultra-léger (sans historique)
RUN git clone --depth 1 https://github.com/cthonney/maptoposter-docker.git .

# 4. Install des deps (Ça passera crème avec Py 3.11)
RUN pip install --no-cache-dir -r requirements.txt


# --- STAGE 2 : RUNTIME (Production) ---
FROM python:3.11-slim

# 1. Lib système requise pour OSMnx/Rtree
# On utilise la version -dev qui est stable sur Debian Bookworm (base de python:3.11)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libspatialindex-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. On récupère le venv et le code du stage 1
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app /app

# 3. Nettoyage de sécurité
RUN rm -rf /app/.git

# 4. Config
ENV PATH="/opt/venv/bin:$PATH"
ENV MPLBACKEND=Agg

EXPOSE 5025

CMD ["python", "app.py"]
FROM python:3.11-slim

# 1. Dépendances système (Git + Libs géographiques)
RUN apt-get update && apt-get install -y \
    git \
    libspatialindex-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. CLONE du Fork (Récupère le code, y compris app.py et les templates)
RUN git clone https://github.com/cthonney/maptoposter-docker.git .

# 3. Installation des dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# 4. Config environnement
ENV MPLBACKEND=Agg

EXPOSE 5000

CMD ["python", "app.py"]
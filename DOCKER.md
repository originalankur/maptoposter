# Docker Deployment Guide

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Rebuild
docker-compose up -d --build
```

### Using Docker Commands

```bash
# Build image
docker build -t maptoposter:latest .

# Run container
docker run -d \
  --name maptoposter \
  -p 8000:8000 \
  -v $(pwd)/posters:/app/posters \
  -v $(pwd)/themes:/app/themes:ro \
  --restart unless-stopped \
  maptoposter:latest

# View logs
docker logs -f maptoposter

# Stop container
docker stop maptoposter
```

## Access Application

- **Web UI**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/themes

## Container Features

- **Multi-stage build**: Optimized image size (~1.8GB)
- **Health checks**: Automatic container health monitoring
- **Auto-restart**: Container restarts on failure
- **Volume mounts**: Persistent poster storage
- **Chinese font support**: Full CJK character support (Noto Sans SC)

## Architecture

### Multi-stage Build
1. **Stage 1**: Node.js builds frontend static files
2. **Stage 2**: Python backend serves API + frontend

### Tech Stack
- Base images: `node:20-alpine`, `python:3.13-slim`
- Web server: FastAPI with uvicorn
- Port: 8000 (unified frontend + backend)
- Fonts: Noto Sans SC TTF (10MB × 3 weights)

## Volume Mounts

```yaml
volumes:
  - ./posters:/app/posters      # Generated posters (read-write)
  - ./themes:/app/themes:ro     # Theme configs (read-only)
```

## Configuration

### Change Port

```bash
# Use port 9000 instead of 8000
docker run -d -p 9000:8000 ...
```

Or edit `docker-compose.yml`:

```yaml
ports:
  - "9000:8000"
```

### Environment Variables

Add to `docker-compose.yml`:

```yaml
environment:
  - PYTHONUNBUFFERED=1
  - CACHE_DIR=/app/cache
```

### Resource Limits

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 2G
    reservations:
      cpus: '1'
      memory: 512M
```

## Troubleshooting

### Port Already in Use

```bash
# Check what's using the port
lsof -i :8000

# Use a different port
docker run -d -p 9000:8000 ...
```

### Build Fails

```bash
# Clean Docker cache
docker builder prune

# Rebuild without cache
docker-compose build --no-cache
```

### Container Exits

```bash
# Check logs
docker logs maptoposter

# Check exit code
docker ps -a | grep maptoposter
```

### Font Errors

If you see "Cannot load face (error 0x2)":

```bash
# Verify fonts in container
docker exec maptoposter ls -lh /app/fonts/

# Should show NotoSansSC-*.ttf files (10MB each)
docker exec maptoposter file /app/fonts/NotoSansSC-Regular.ttf
# Output: TrueType Font data
```

## Maintenance

### View Container Stats

```bash
docker stats maptoposter
```

### Enter Container Shell

```bash
docker exec -it maptoposter /bin/bash
```

### Cleanup

```bash
# Stop and remove container
docker stop maptoposter && docker rm maptoposter

# Remove image
docker rmi maptoposter:latest

# Remove unused images
docker image prune
```

### Update Application

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

## Production Deployment

### Security

1. **Use non-root user**:
```yaml
user: "1000:1000"
```

2. **Read-only filesystem**:
```yaml
read_only: true
tmpfs:
  - /tmp
```

3. **Limit network access**:
```yaml
ports:
  - "127.0.0.1:8000:8000"  # localhost only
```

### Reverse Proxy (Nginx)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### HTTPS with Let's Encrypt

```bash
# Install certbot
apt-get install certbot python3-certbot-nginx

# Get certificate
certbot --nginx -d your-domain.com

# Auto-renewal
certbot renew --dry-run
```

## System Requirements

### Minimum
- Docker: 20.10+
- Docker Compose: 2.0+
- CPU: 2 cores
- RAM: 2 GB
- Disk: 5 GB free space

### Recommended
- CPU: 4 cores
- RAM: 4 GB
- Disk: 10 GB free space
- Network: Stable internet connection

## Performance

### Image Size
```
Total: ~1.8 GB
├─ Python base: ~400 MB
├─ Python deps: ~800 MB
├─ System deps: ~200 MB
├─ Frontend: ~5 MB
└─ Fonts: ~30 MB
```

### Runtime Resources
- **CPU**: 1-2 cores (peaks during generation)
- **Memory**: 512 MB - 2 GB (depends on map complexity)
- **Disk**: Grows with poster count (~2-10 MB per poster)

### Generation Time
- Simple map: 15-30 seconds
- Complex map: 30-60 seconds
- Depends on: City size, theme, network speed

## Docker Compose Configuration

Complete `docker-compose.yml` example:

```yaml
version: '3.8'

services:
  maptoposter:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: maptoposter
    ports:
      - "8000:8000"
    volumes:
      - ./posters:/app/posters
      - ./themes:/app/themes:ro
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/').raise_for_status()"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G

networks:
  default:
    name: maptoposter-network
```

## Common Commands

```bash
# Build
docker-compose build
docker build -t maptoposter:latest .

# Start
docker-compose up -d
docker start maptoposter

# Stop
docker-compose down
docker stop maptoposter

# Logs
docker-compose logs -f
docker logs -f maptoposter

# Shell
docker exec -it maptoposter /bin/bash

# Stats
docker stats maptoposter

# Inspect
docker inspect maptoposter

# Export/Import
docker save maptoposter:latest > maptoposter.tar
docker load < maptoposter.tar
```

## Support

For issues:
- Check container logs: `docker logs maptoposter`
- Verify health: `docker ps | grep maptoposter`
- View API docs: http://localhost:8000/docs
- Read README: [README.md](./README.md)

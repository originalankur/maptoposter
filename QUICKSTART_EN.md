# Quick Start Guide

## Installation

### Prerequisites
- Python 3.11+ (but < 3.14)
- Node.js 18+
- npm or yarn

### Install Dependencies

```bash
# Python dependencies (using uv - recommended)
uv sync --locked

# Or using pip
pip install -r requirements.txt

# Frontend dependencies
cd webapp
npm install
cd ..
```

## Start Application

### Method 1: One-Command Startup (Recommended)

```bash
./start.sh
```

This starts both backend and frontend automatically.

### Method 2: Manual Startup

```bash
# Terminal 1: Start backend
uv run python api_server.py
# Or: python api_server.py

# Terminal 2: Start frontend
cd webapp
npm run dev
```

### Method 3: Docker (Easiest)

```bash
# Build and start
docker-compose up -d

# Access at http://localhost:8000
```

## Access Application

- **Web UI**: http://localhost:3000 (dev) or http://localhost:8000 (Docker)
- **API Docs**: http://localhost:8000/docs
- **Backend**: http://localhost:8000

## Usage

### Using Web Interface

1. Open http://localhost:3000 in your browser
2. Search for a city (supports Chinese, English, Japanese, etc.)
3. Select city from dropdown list
4. Choose a theme (17 available)
5. Adjust map radius (optional)
6. Click "Generate Poster"
7. Wait for progress bar to complete (15-60 seconds)
8. Download your poster

### Using Command Line

```bash
# Generate a poster
uv run python create_map_poster.py \
  --city "New York" \
  --country "USA" \
  --theme noir \
  --output my_poster.png

# List available themes
uv run python create_map_poster.py --list-themes

# Use custom coordinates
uv run python create_map_poster.py \
  --latitude 40.7128 \
  --longitude -74.0060 \
  --theme ocean
```

### Using API

```bash
# Generate poster
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "city": "Tokyo",
    "country": "Japan",
    "theme": "japanese_ink"
  }'

# List themes
curl http://localhost:8000/api/themes

# List generated posters
curl http://localhost:8000/api/posters

# Download poster
curl http://localhost:8000/api/posters/tokyo_japanese_ink_20260128.png \
  -o my_poster.png
```

## Features

### Multilingual Support
- Interface: English, Chinese (Simplified)
- City search: Supports multiple languages
- Font: Noto Sans SC (full CJK support)

### 17 Themes Available
- `noir` - Pure black & white modern gallery style
- `ocean` - Various blues and teals (perfect for coastal cities)
- `terracotta` - Mediterranean warmth with burnt orange tones
- `sunset` - Warm oranges and pinks on soft peach
- `blueprint` - Classic architectural blueprint style
- `forest` - Deep greens and sage tones
- `midnight_blue` - Deep navy with gold/copper roads
- `neon_cyberpunk` - Dark with electric pink/cyan
- `japanese_ink` - Traditional ink wash inspired
- `pastel_dream` - Soft muted pastels with dusty blues
- And 7 more!

### City Search
- Global city database (OpenStreetMap)
- Autocomplete with 300ms debounce
- Multilingual search support
- Automatic coordinate filling

### Progress Tracking
- Real-time progress bar
- 4 steps: Find coordinates → Download data → Render → Complete
- Estimated time display

### Poster Gallery
- View all generated posters
- Click to switch preview
- Download or delete posters
- Shows creation date and file size

## Configuration

### Customize Themes

Edit or create JSON files in `themes/` directory:

```json
{
  "name": "My Custom Theme",
  "description": "My awesome color scheme",
  "bg": "#FFFFFF",
  "text": "#000000",
  "water": "#4A90E2",
  "parks": "#7ED321",
  "road_motorway": "#FF5722"
}
```

### Adjust Map Settings

```bash
# Larger map radius (default: 18000 meters)
--distance 25000

# Different image size (default: 12x16 inches)
--width 18 --height 24

# Custom fonts
--font-family "Roboto"
```

## Troubleshooting

### Backend Won't Start

```bash
# Check if port 8000 is available
lsof -i :8000

# Verify Python version
python --version  # Should be 3.11-3.13

# Reinstall dependencies
uv sync --locked
```

### Frontend Won't Start

```bash
# Check if port 3000 is available
lsof -i :3000

# Clear npm cache and reinstall
cd webapp
rm -rf node_modules package-lock.json
npm install
```

### City Search Fails

- Check internet connection
- Verify backend is running
- Look for CORS errors in browser console
- Try a different city name or language

### Chinese Characters Show as Boxes

```bash
# Verify Chinese fonts are installed
ls -lh fonts/NotoSansSC-*.ttf

# Should show 3 files (10MB each)
# If missing, restart application or rebuild Docker
```

### Generation Takes Too Long

- Large cities take longer (30-60 seconds)
- Check internet connection
- Look at backend logs for errors
- Try a smaller radius value

## Development

### Project Structure

```
maptoposter/
├── create_map_poster.py    # Main generation script
├── api_server.py           # FastAPI backend
├── font_management.py      # Font handling
├── start.sh               # Startup script
├── fonts/                 # Font files
├── themes/                # Theme JSON files
├── posters/               # Generated posters
└── webapp/                # React frontend
    ├── src/
    │   ├── components/    # React components
    │   ├── i18n/         # Translations
    │   └── App.tsx       # Main app
    └── package.json
```

### Running Tests

```bash
# Test all theme variations
./test/all_variations.sh

# Manual test
uv run python create_map_poster.py \
  --city "Tokyo" \
  --country "Japan" \
  --theme noir
```

### Build for Production

```bash
# Build frontend
cd webapp
npm run build
cd ..

# Frontend files will be in webapp/dist/
# Backend serves these automatically

# Or use Docker for all-in-one deployment
docker build -t maptoposter:latest .
```

## Tips

### Best Practices

1. **Choose right theme for city**:
   - Coastal cities: `ocean`, `blueprint`
   - Dense urban: `noir`, `midnight_blue`
   - Historic cities: `japanese_ink`, `warm_beige`
   - Modern cities: `neon_cyberpunk`, `gradient_roads`

2. **Adjust map radius**:
   - Small towns: 8,000-12,000 meters
   - Medium cities: 15,000-20,000 meters
   - Large cities: 20,000-30,000 meters

3. **Print settings**:
   - Default size: 12×16 inches (perfect)
   - Resolution: 300 DPI (built-in)
   - Paper: Matte art paper or canvas
   - Frame: Simple black or white frame

### Common Use Cases

```bash
# Coastal city poster
./create_map_poster.py --city "Miami" --theme ocean

# Japanese city with traditional theme
./create_map_poster.py --city "Kyoto" --theme japanese_ink

# Chinese city with Chinese text
curl -X POST http://localhost:8000/api/generate -d '{
  "city": "Beijing",
  "country": "China",
  "display_city": "北京",
  "display_country": "中国",
  "theme": "terracotta"
}'

# Large custom area
./create_map_poster.py \
  --latitude 51.5074 \
  --longitude -0.1278 \
  --distance 30000 \
  --theme blueprint
```

## Next Steps

- Read [README.md](./README.md) for detailed documentation
- Read [DOCKER.md](./DOCKER.md) for Docker deployment
- Read [WEBUI_README.md](./WEBUI_README.md) for Web UI details
- Explore themes in `themes/` directory
- Check [CHANGELOG.md](./CHANGELOG.md) for updates

## Support

- GitHub Issues: Report bugs and feature requests
- API Documentation: http://localhost:8000/docs
- Check logs: `docker logs maptoposter` or console output

Enjoy creating beautiful map posters! 🗺️✨

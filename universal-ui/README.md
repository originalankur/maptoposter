# Universal UI for Maptoposter (Dual Mode)

> A local, universal interface that works on any OS without cloud services - with **automatic generation** OR **manual command** modes.

## 🎯 Purpose

This Universal UI provides TWO ways to generate map posters:

**MODE A (Automatic)**: One-click generation via local HTTP server  
**MODE B (Manual)**: Copy-paste terminal command (always available)

Both modes:
- Work entirely offline
- Require no cloud services or APIs
- Keep the core Python script untouched
- Support macOS, Windows, and Linux

## ⚡ Quick Start

### Option 1: Automatic Mode (Recommended)

**Step 1:** Install dependencies
```bash
pip install -r requirements.txt
pip install flask flask-cors
```

**Step 2:** Start the local server
```bash
python universal-ui/runner/run_local.py --serve
```

You should see:
```
╔════════════════════════════════════════════════════════════╗
║  Maptoposter Local Server                                  ║
║  Server running at: http://127.0.0.1:8000                 ║
╚════════════════════════════════════════════════════════════╝
```

**Step 3:** Open the web UI
```bash
# macOS
open universal-ui/web/index.html

# Linux
xdg-open universal-ui/web/index.html

# Windows
start universal-ui/web/index.html
```

**Step 4:** Generate posters with one click!
- Fill in city name
- Select theme and radius
- Click "Generate Poster"
- Wait a few minutes
- Click "Load Poster" to view

### Option 2: Manual Mode (Fallback)

**Step 1:** Open the web UI (same as above)

**Step 2:** The UI will show "Server Offline" - that's OK!

**Step 3:** Fill in the form and click "Show Command"

**Step 4:** Copy the generated command and run it in your terminal:
```bash
python3 universal-ui/runner/run_local.py --city "Paris" --theme "noir"
```

**Step 5:** Load the generated poster using "Load Poster" button

## 📦 What's Inside

```
universal-ui/
├── runner/
│   └── run_local.py       # Dual-mode runner (CLI + Server)
├── web/
│   ├── index.html         # Web interface with server detection
│   ├── style.css          # Professional styling
│   ├── app.js             # Dual-mode application logic
│   └── themes.js          # 17 available themes
├── tauri/                 # Native desktop app scaffold
└── README.md              # This file
```

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  WEB UI (index.html)                                     │
│                                                          │
│  On Load: Pings http://127.0.0.1:8000/health            │
│                                                          │
├──────────────┬───────────────────────────────────────────┤
│              │                                           │
│  ✓ Server    │  ✗ No Server                             │
│   Found      │   Detected                               │
│              │                                           │
│  MODE A      │  MODE B                                   │
│  Automatic   │  Manual                                   │
│              │                                           │
│  POST to     │  Generate                                 │
│  /generate   │  Command                                  │
│              │                                           │
└──────┬───────┴──────┬────────────────────────────────────┘
       │              │
       ▼              ▼
┌──────────────────────────────────────────────────────────┐
│  run_local.py (Dual Mode)                                │
│                                                          │
│  --serve      ← HTTP Server (Flask)                      │
│  --city X     ← CLI Mode                                 │
│                                                          │
└──────────────────┬───────────────────────────────────────┘
                   │ Calls as subprocess
                   ▼
┌──────────────────────────────────────────────────────────┐
│  create_map_poster.py (UNCHANGED)                        │
└──────────────────┬───────────────────────────────────────┘
                   │ Outputs
                   ▼
┌──────────────────────────────────────────────────────────┐
│  posters/your_map.png                                    │
└──────────────────────────────────────────────────────────┘
```

## 🛠️ Runner Modes

### CLI Mode (Default)

Run directly from command line:

```bash
# Basic usage
python3 universal-ui/runner/run_local.py --city "Tokyo"

# With all options
python3 universal-ui/runner/run_local.py \
    --city "Berlin" \
    --country "Germany" \
    --theme "noir" \
    --radius 5000
```

**Arguments:**
- `--city` (required) - City name
- `--country` (optional) - Country name
- `--theme` (optional) - Theme name (default: feature_based)
- `--radius` (optional) - Map radius in meters

**Output:**
- On success: Prints ONLY the file path to stdout
- On error: Prints error message to stderr

### Server Mode

Run as HTTP server:

```bash
# Start on default port (8000)
python3 universal-ui/runner/run_local.py --serve

# Custom port
python3 universal-ui/runner/run_local.py --serve --port 3000
```

**Endpoints:**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Check if server is running |
| `/themes` | GET | List available themes |
| `/generate` | POST | Generate poster |

**Example POST to /generate:**
```json
{
  "city": "Paris",
  "country": "France",
  "theme": "noir",
  "radius": 5000
}
```

**Response:**
```json
{
  "status": "ok",
  "message": "Poster generated successfully",
  "image_path": "/path/to/posters/paris_noir_20260118_143022.png"
}
```

## 🎨 Available Themes

All 17 themes from the `themes/` directory are available:

- **feature_based** (default) - Color by feature type
- **midnight_blue** - Dark blue night theme
- **noir** - Classic black and white
- **ocean** - Ocean blues and teals
- **sunset** - Warm sunset tones
- **forest** - Deep forest greens
- **autumn** - Warm autumn colors
- **blueprint** - Classic blueprint style
- **contrast_zones** - High contrast zones
- **copper_patina** - Aged copper aesthetic
- **gradient_roads** - Roads with gradient colors
- **japanese_ink** - Traditional ink painting style
- **monochrome_blue** - Single-color blue theme
- **neon_cyberpunk** - Bright neon colors
- **pastel_dream** - Soft pastel colors
- **terracotta** - Earthy terracotta
- **warm_beige** - Neutral warm beige

## 🖥️ Desktop App (Future)

The `tauri/` directory contains a scaffold for a native desktop application that would:

1. Launch the Python server automatically
2. Open the web UI in a native window
3. Provide seamless one-click generation
4. Work entirely offline

**Status:** Configuration only - not yet buildable.

See [`tauri/README.md`](tauri/README.md) for details.

## 📋 Requirements

**Python:**
- Python 3.6+
- All dependencies from root `requirements.txt`
- Additional for server mode: `flask`, `flask-cors`

**Install all dependencies:**
```bash
pip install -r requirements.txt
pip install flask flask-cors
```

**Browser:**
- Any modern browser (Chrome, Firefox, Safari, Edge)
- Works with `file://` protocol

## ⚠️ Important Notes

### Core Logic NOT Modified

**The existing `create_map_poster.py` script was NOT modified.** This UI layer:
- Is completely separate
- Calls the original script via subprocess only
- Can be removed without breaking anything
- Doesn't import or change core functionality

You can still use the original script directly:
```bash
python create_map_poster.py --city "London" --country "UK"
```

### Limitations & Design Choices

1. **Server must be started manually** (or use Tauri desktop app when complete)
   - This is intentional for simplicity and security
   - No persistent background processes
   
2. **Image loading is manual** (click "Load Poster" and select file)
   - Browser security prevents automatic file access
   - This ensures cross-browser compatibility

3. **Radius parameter not yet fully supported**
   - Core script needs to be updated to accept `--distance` parameter
   - UI documents this for future enhancement

## 🚀 Advanced Usage

### Custom Server Configuration

```bash
# Different port
python3 universal-ui/runner/run_local.py --serve --port 9000

# Different host (allow network access - use with caution!)
python3 universal-ui/runner/run_local.py --serve --host 0.0.0.0
```

### Batch Generation

Use CLI mode in a script:

```bash
#!/bin/bash
cities=("Paris" "Tokyo" "Berlin" "New York")

for city in "${cities[@]}"; do
    echo "Generating $city..."
    python3 universal-ui/runner/run_local.py \
        --city "$city" \
        --theme "noir"
done
```

### Development Server

For development with auto-reload:

```bash
# Install additional dev dependencies
pip install flask[async] watchdog

# Run with Flask development mode
FLASK_ENV=development python3 universal-ui/runner/run_local.py --serve
```

## 🐛 Troubleshooting

### Server won't start

**Error:** `Flask not installed`

**Solution:**
```bash
pip install flask flask-cors
```

### Port already in use

**Error:** `Address already in use`

**Solution:** Use a different port
```bash
python3 universal-ui/runner/run_local.py --serve --port 8080
```

### Browser shows "Server Offline"

This is **not an error** - it means you're in Manual Mode. Either:
1. Start the server (see Quick Start)
2. Or use Manual Mode (copy-paste commands)

### CORS errors in browser console

If you see CORS errors, make sure:
1. Flask-CORS is installed: `pip install flask-cors`
2. You're opening the UI via `file://` protocol, not `http://`

## 📈 Roadmap

Future enhancements:

- [ ] **Auto-detect themes**: Scan `themes/` folder dynamically
- [ ] **Progress streaming**: Real-time generation progress
- [ ] **Radius support**: Update core script to accept custom radius
- [ ] **Batch generation UI**: Generate multiple cities at once
- [ ] **History view**: Browse previously generated posters
- [ ] **Tauri app**: Complete the native desktop application
- [ ] **Auto-update**: Keep themes in sync with folder
- [ ] **Preset management**: Save favorite configurations

## 🤝 Contributing

When adding features:

1. **Keep it local**: No cloud dependencies
2. **Respect core**: Don't modify `create_map_poster.py`
3. **Dual mode**: Support both automatic and manual modes
4. **Test everywhere**: Verify on multiple OS

## 📄 License

Same license as the parent maptoposter project.

## 🙏 Acknowledgments

Built to complement the excellent maptoposter tool while:
- Respecting its architecture
- Maintaining backward compatibility
- Adding optional convenience features
- Supporting multiple usage patterns

---

**Built with ❤️ for the maptoposter community**

**Dual Mode**: Power when you need it, simplicity when you don't.

# Map Poster Generator - Web UI

A modern web interface for generating beautiful, minimalist map posters.

## Quick Start

### 1. Install Python Dependencies

```bash
# Using uv (recommended)
uv sync --locked

# Or using pip
pip install -r requirements.txt
```

### 2. Install Frontend Dependencies

```bash
cd webapp
npm install
```

### 3. Run the Application

Start both the backend API and frontend development server:

```bash
# Terminal 1: Start backend
uv run python api_server.py

# Terminal 2: Start frontend
cd webapp
npm run dev
```

Then open [http://localhost:3000](http://localhost:3000) in your browser.

## Features

- 🗺️ Generate map posters for any city in the world
- 🎨 17 beautiful theme styles to choose from
- 📏 Adjustable map radius (4km - 20km)
- 📐 Custom dimensions for various use cases
- 🌍 Multi-language support with custom fonts
- 🖼️ Preview and download generated posters
- 🗑️ Manage generated posters

## API Documentation

Once the backend is running, visit [http://localhost:8000/docs](http://localhost:8000/docs) for interactive API documentation.

## Project Structure

```
maptoposter/
├── api_server.py              # FastAPI backend
├── create_map_poster.py       # Core poster generation logic
├── webapp/                    # React frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── App.tsx           # Main application
│   │   └── main.tsx          # Entry point
│   └── package.json          # Frontend dependencies
├── themes/                    # Theme JSON files
└── posters/                   # Generated posters
```

## Usage

1. Enter city and country name
2. Select a theme from the available options
3. Adjust the map radius if needed
4. (Optional) Configure advanced options
5. Click "Generate Poster" and wait for the result
6. Download or manage your posters
"""
Web UI for Map Poster Generator
Features:
- Address search with autocomplete
- Live progress updates via Server-Sent Events
- Multiple image formats (PNG, SVG, PDF)
- Building layer support
- Theme selection
- Various poster sizes
"""

from flask import Flask, render_template, request, jsonify, Response, send_file, url_for
from flask_cors import CORS
import osmnx as ox
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import matplotlib.colors as mcolors
import numpy as np
from geopy.geocoders import Nominatim
import json
import os
import re
import time
import threading
import queue
import tempfile
import shutil
import logging
from datetime import datetime
from pathlib import Path
from hashlib import md5
import pickle
from typing import Generator
import uuid

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

app = Flask(__name__)

# Restrict CORS via environment variable instead of allowing all
ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:5000,http://127.0.0.1:5000,http://localhost:3000,http://127.0.0.1:3000",
)
ALLOWED_ORIGINS = [origin.strip() for origin in ALLOWED_ORIGINS.split(",") if origin.strip()]
CORS(app, origins=ALLOWED_ORIGINS)

# ==================== Configuration ====================
CACHE_DIR_PATH = os.environ.get("CACHE_DIR", "cache")
CACHE_DIR = Path(CACHE_DIR_PATH)
CACHE_DIR.mkdir(exist_ok=True)

THEMES_DIR = "themes"
FONTS_DIR = "fonts"
POSTERS_DIR = "posters"  # For example posters only
TEMP_DIR = Path(tempfile.gettempdir()) / "maptoposter_temp"
MAX_DISTANCE_METERS = 50_000
THEME_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
NOMINATIM_USER_AGENT = os.environ.get(
    "NOMINATIM_USER_AGENT",
    "maptoposter_web (contact: contact@example.com)",
)

# Create directories
Path(POSTERS_DIR).mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)
POSTERS_PATH = Path(POSTERS_DIR).resolve()

# Note: cache uses pickle. Keep cache directory non-writable by untrusted users.

# Rate limiting for external API calls (Nominatim and OSM data)
REQUEST_LOCK = threading.Lock()
LAST_REQUEST_TIME = 0.0
MIN_REQUEST_INTERVAL = float(os.environ.get("REQUEST_MIN_INTERVAL", "1.0"))


def wait_for_rate_limit(min_interval: float = MIN_REQUEST_INTERVAL) -> None:
    """Enforce a simple per-process rate limit for external requests."""
    global LAST_REQUEST_TIME
    with REQUEST_LOCK:
        now = time.monotonic()
        delta = now - LAST_REQUEST_TIME
        if delta < min_interval:
            time.sleep(min_interval - delta)
        LAST_REQUEST_TIME = time.monotonic()


class ProgressStore:
    """Thread-safe progress queue store with stale cleanup."""

    def __init__(self, ttl_seconds: int = 900):
        self._lock = threading.RLock()
        self._data: dict[str, dict[str, object]] = {}
        self._ttl = ttl_seconds

    def create(self, job_id: str) -> queue.Queue:
        with self._lock:
            q: queue.Queue = queue.Queue()
            self._data[job_id] = {"queue": q, "updated": time.time()}
            return q

    def put(self, job_id: str, payload: dict) -> None:
        with self._lock:
            entry = self._data.get(job_id)
            if not entry:
                return
            queue_obj: queue.Queue = entry["queue"]  # type: ignore[assignment]
            queue_obj.put(payload)
            entry["updated"] = time.time()

    def get_queue(self, job_id: str) -> queue.Queue | None:
        with self._lock:
            entry = self._data.get(job_id)
            if entry:
                entry["updated"] = time.time()
                return entry["queue"]  # type: ignore[return-value]
            return None

    def delete(self, job_id: str) -> None:
        with self._lock:
            self._data.pop(job_id, None)

    def touch(self, job_id: str) -> None:
        with self._lock:
            if job_id in self._data:
                self._data[job_id]["updated"] = time.time()

    def cleanup(self) -> list[str]:
        now = time.time()
        removed: list[str] = []
        with self._lock:
            for job_id, entry in list(self._data.items()):
                if now - entry.get("updated", 0) > self._ttl:
                    removed.append(job_id)
                    self._data.pop(job_id, None)
        return removed


progress_store = ProgressStore()


def _start_progress_cleanup_thread() -> None:
    def _cleanup_loop():
        while True:
            time.sleep(300)
            removed = progress_store.cleanup()
            if removed:
                logging.debug("Cleaned stale jobs: %s", ",".join(removed))

    threading.Thread(target=_cleanup_loop, daemon=True).start()


_start_progress_cleanup_thread()

# Store for temporary downloads (job_id -> filepath)
temp_downloads: dict[str, str] = {}

# Poster size presets (width x height in inches)
POSTER_SIZES = {
    "A4": (8.27, 11.69),
    "A3": (11.69, 16.54),
    "A2": (16.54, 23.39),
    "Square": (12, 12),
    "Wide": (16, 9),
    "Portrait": (12, 16),
    "Landscape": (16, 12),
}

# ==================== Cache Functions ====================
def cache_file(key: str) -> str:
    encoded = md5(key.encode()).hexdigest()
    return f"{encoded}.pkl"

def cache_get(name: str):
    path = CACHE_DIR / cache_file(name)
    if path.exists():
        with path.open("rb") as f:
            return pickle.load(f)
    return None

def cache_set(name: str, obj) -> None:
    path = CACHE_DIR / cache_file(name)
    try:
        with path.open("wb") as f:
            pickle.dump(obj, f)
    except Exception as e:
        logging.warning("Cache error: %s", e)

# ==================== Font Functions ====================
def load_fonts():
    fonts = {
        'bold': os.path.join(FONTS_DIR, 'Roboto-Bold.ttf'),
        'regular': os.path.join(FONTS_DIR, 'Roboto-Regular.ttf'),
        'light': os.path.join(FONTS_DIR, 'Roboto-Light.ttf')
    }
    for weight, path in fonts.items():
        if not os.path.exists(path):
            print(f"⚠ Font not found: {path}")
            return None
    return fonts

FONTS = load_fonts()

# ==================== Theme Functions ====================
def get_available_themes():
    if not os.path.exists(THEMES_DIR):
        return []
    themes = []
    for file in sorted(os.listdir(THEMES_DIR)):
        if file.endswith('.json'):
            theme_name = file[:-5]
            themes.append(theme_name)
    return themes

def load_theme(theme_name="feature_based"):
    if not THEME_NAME_PATTERN.match(theme_name):
        raise ValueError("Invalid theme name")

    theme_file = os.path.join(THEMES_DIR, f"{theme_name}.json")
    if not os.path.exists(theme_file):
        return {
            "name": "Default",
            "bg": "#FFFFFF",
            "text": "#000000",
            "gradient_color": "#FFFFFF",
            "water": "#C0C0C0",
            "parks": "#F0F0F0",
            "buildings": "#E0E0E0",
            "road_motorway": "#0A0A0A",
            "road_primary": "#1A1A1A",
            "road_secondary": "#2A2A2A",
            "road_tertiary": "#3A3A3A",
            "road_residential": "#4A4A4A",
            "road_default": "#3A3A3A"
        }
    with open(theme_file, 'r') as f:
        theme = json.load(f)
        # Add default building color if not present
        if 'buildings' not in theme:
            theme['buildings'] = '#E0E0E0'
        return theme

def get_themes_with_details():
    themes = []
    for theme_name in get_available_themes():
        theme_data = load_theme(theme_name)
        themes.append({
            'id': theme_name,
            'name': theme_data.get('name', theme_name),
            'description': theme_data.get('description', ''),
            'bg': theme_data.get('bg', '#FFFFFF'),
            'text': theme_data.get('text', '#000000')
        })
    return themes


def safe_path(base_dir: Path, filename: str) -> Path | None:
    """Prevent path traversal outside base_dir."""
    base_resolved = base_dir.resolve()
    try:
        candidate = (base_resolved / filename).resolve()
        candidate.relative_to(base_resolved)
    except Exception:
        return None
    return candidate

# ==================== Progress Updates ====================
def send_progress(job_id: str, step: str, progress: int, message: str) -> None:
    """Send progress update to client."""
    progress_store.put(job_id, {
        'step': step,
        'progress': progress,
        'message': message
    })


def send_complete(job_id: str, filename: str, download_url: str) -> None:
    """Send completion message to client."""
    progress_store.put(job_id, {
        'step': 'complete',
        'progress': 100,
        'message': 'Poster successfully created!',
        'filename': filename,
        'download_url': download_url
    })


def send_error(job_id: str, error_message: str) -> None:
    """Send error message to client."""
    progress_store.put(job_id, {
        'step': 'error',
        'progress': 0,
        'message': error_message
    })

# ==================== Map Generation Functions ====================
def get_edge_colors_by_type(G, theme):
    edge_colors = []
    for u, v, data in G.edges(data=True):
        highway = data.get('highway', 'unclassified')
        if isinstance(highway, list):
            highway = highway[0] if highway else 'unclassified'
        
        if highway in ['motorway', 'motorway_link']:
            color = theme['road_motorway']
        elif highway in ['trunk', 'trunk_link', 'primary', 'primary_link']:
            color = theme['road_primary']
        elif highway in ['secondary', 'secondary_link']:
            color = theme['road_secondary']
        elif highway in ['tertiary', 'tertiary_link']:
            color = theme['road_tertiary']
        elif highway in ['residential', 'living_street', 'unclassified']:
            color = theme['road_residential']
        else:
            color = theme['road_default']
        edge_colors.append(color)
    return edge_colors

def get_edge_widths_by_type(G):
    edge_widths = []
    for u, v, data in G.edges(data=True):
        highway = data.get('highway', 'unclassified')
        if isinstance(highway, list):
            highway = highway[0] if highway else 'unclassified'
        
        if highway in ['motorway', 'motorway_link']:
            width = 1.2
        elif highway in ['trunk', 'trunk_link', 'primary', 'primary_link']:
            width = 1.0
        elif highway in ['secondary', 'secondary_link']:
            width = 0.8
        elif highway in ['tertiary', 'tertiary_link']:
            width = 0.6
        else:
            width = 0.4
        edge_widths.append(width)
    return edge_widths

def create_gradient_fade(ax, color, location='bottom', zorder=10):
    vals = np.linspace(0, 1, 256).reshape(-1, 1)
    gradient = np.hstack((vals, vals))
    
    rgb = mcolors.to_rgb(color)
    my_colors = np.zeros((256, 4))
    my_colors[:, 0] = rgb[0]
    my_colors[:, 1] = rgb[1]
    my_colors[:, 2] = rgb[2]
    
    if location == 'bottom':
        my_colors[:, 3] = np.linspace(1, 0, 256)
        extent_y_start = 0
        extent_y_end = 0.25
    else:
        my_colors[:, 3] = np.linspace(0, 1, 256)
        extent_y_start = 0.75
        extent_y_end = 1.0

    custom_cmap = mcolors.ListedColormap(my_colors)
    
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    y_range = ylim[1] - ylim[0]
    
    y_bottom = ylim[0] + y_range * extent_y_start
    y_top = ylim[0] + y_range * extent_y_end
    
    ax.imshow(gradient, extent=[xlim[0], xlim[1], y_bottom, y_top], 
              aspect='auto', cmap=custom_cmap, zorder=zorder, origin='lower')

def get_crop_limits(G, fig):
    xs = [data['x'] for _, data in G.nodes(data=True)]
    ys = [data['y'] for _, data in G.nodes(data=True)]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    x_range = maxx - minx
    y_range = maxy - miny

    fig_width, fig_height = fig.get_size_inches()
    desired_aspect = fig_width / fig_height
    current_aspect = x_range / y_range

    center_x = (minx + maxx) / 2
    center_y = (miny + maxy) / 2

    if current_aspect > desired_aspect:
        desired_x_range = y_range * desired_aspect
        new_minx = center_x - desired_x_range / 2
        new_maxx = center_x + desired_x_range / 2
        crop_xlim = (new_minx, new_maxx)
        crop_ylim = (miny, maxy)
    elif current_aspect < desired_aspect:
        desired_y_range = x_range / desired_aspect
        new_miny = center_y - desired_y_range / 2
        new_maxy = center_y + desired_y_range / 2
        crop_xlim = (minx, maxx)
        crop_ylim = (new_miny, new_maxy)
    else:
        crop_xlim = (minx, maxx)
        crop_ylim = (miny, maxy)
    
    return crop_xlim, crop_ylim

def fetch_graph(point, dist, job_id):
    lat, lon = point
    graph_key = f"graph_{lat}_{lon}_{dist}"
    cached = cache_get(graph_key)
    if cached is not None:
        send_progress(job_id, 'fetch_streets', 20, 'Street network loaded from cache')
        return cached

    try:
        wait_for_rate_limit()
        G = ox.graph_from_point(point, dist=dist, dist_type='bbox', network_type='all')
        cache_set(graph_key, G)
        return G
    except Exception as e:
        logging.error("Error fetching graph: %s", e)
        return None

def fetch_features(point, dist, tags, name, job_id, progress_step, progress_value, progress_msg):
    lat, lon = point
    tag_str = "_".join(tags.keys())
    features_key = f"{name}_{lat}_{lon}_{dist}_{tag_str}"
    cached = cache_get(features_key)
    if cached is not None:
        send_progress(job_id, progress_step, progress_value, f'{progress_msg} (aus Cache)')
        return cached

    try:
        wait_for_rate_limit()
        data = ox.features_from_point(point, tags=tags, dist=dist)
        cache_set(features_key, data)
        return data
    except Exception as e:
        logging.error("Error fetching %s: %s", name, e)
        return None

def generate_poster(job_id: str, params: dict):
    """Generate the map poster in a background thread."""
    try:
        city = params['city']
        country = params.get('country', '')
        lat = params['lat']
        lon = params['lon']
        dist = params.get('distance', 10000)
        theme_name = params.get('theme', 'feature_based')
        output_format = params.get('format', 'png')
        poster_size = params.get('size', 'Portrait')
        include_buildings = params.get('buildings', False)
        
        theme = load_theme(theme_name)
        point = (lat, lon)
        
        # Get poster dimensions
        fig_size = POSTER_SIZES.get(poster_size, (12, 16))
        
        # Step 1: Fetch Street Network (0-20%)
        send_progress(job_id, 'fetch_streets', 5, 'Loading street network...')
        G = fetch_graph(point, dist, job_id)
        if G is None:
            send_error(job_id, 'Street network could not be loaded')
            return
        send_progress(job_id, 'fetch_streets', 20, 'Street network loaded')
        
        # Step 2: Fetch Water Features (20-35%)
        send_progress(job_id, 'fetch_water', 25, 'Loading water features...')
        water = fetch_features(point, dist, {'natural': 'water', 'waterway': 'riverbank'}, 'water',
                      job_id, 'fetch_water', 35, 'Water features loaded')
        
        # Step 3: Fetch Parks (35-50%)
        send_progress(job_id, 'fetch_parks', 40, 'Loading parks...')
        parks = fetch_features(point, dist, {'leisure': 'park', 'landuse': 'grass'}, 'parks',
                      job_id, 'fetch_parks', 50, 'Parks loaded')
        
        # Step 4: Fetch Buildings if enabled (50-65%)
        buildings = None
        if include_buildings:
            send_progress(job_id, 'fetch_buildings', 55, 'Loading buildings...')
            buildings = fetch_features(point, dist, {'building': True}, 'buildings',
                                       job_id, 'fetch_buildings', 65, 'Buildings loaded')
        else:
            send_progress(job_id, 'fetch_buildings', 65, 'Buildings skipped')
        
        # Step 5: Render Map (65-90%)
        send_progress(job_id, 'render', 70, 'Rendering map...')
        
        fig, ax = plt.subplots(figsize=fig_size, facecolor=theme['bg'])
        ax.set_facecolor(theme['bg'])
        ax.set_position((0.0, 0.0, 1.0, 1.0))
        
        # Project graph
        G_proj = ox.project_graph(G)
        
        send_progress(job_id, 'render', 75, 'Drawing layers...')
        
        # Plot water
        if water is not None and not water.empty:
            water_polys = water[water.geometry.type.isin(['Polygon', 'MultiPolygon'])]
            if not water_polys.empty:
                try:
                    water_polys = ox.projection.project_gdf(water_polys)
                except Exception:
                    water_polys = water_polys.to_crs(G_proj.graph['crs'])
                water_polys.plot(ax=ax, facecolor=theme['water'], edgecolor='none', zorder=1)
        
        # Plot parks
        if parks is not None and not parks.empty:
            parks_polys = parks[parks.geometry.type.isin(['Polygon', 'MultiPolygon'])]
            if not parks_polys.empty:
                try:
                    parks_polys = ox.projection.project_gdf(parks_polys)
                except Exception:
                    parks_polys = parks_polys.to_crs(G_proj.graph['crs'])
                parks_polys.plot(ax=ax, facecolor=theme['parks'], edgecolor='none', zorder=2)
        
        send_progress(job_id, 'render', 80, 'Drawing buildings...')
        
        # Plot buildings
        if include_buildings and buildings is not None and not buildings.empty:
            building_polys = buildings[buildings.geometry.type.isin(['Polygon', 'MultiPolygon'])]
            if not building_polys.empty:
                try:
                    building_polys = ox.projection.project_gdf(building_polys)
                except Exception:
                    building_polys = building_polys.to_crs(G_proj.graph['crs'])
                building_color = theme.get('buildings', '#E0E0E0')
                building_polys.plot(ax=ax, facecolor=building_color, edgecolor='none', zorder=3, alpha=0.7)
        
        send_progress(job_id, 'render', 85, 'Drawing streets...')
        
        # Plot roads
        edge_colors = get_edge_colors_by_type(G_proj, theme)
        edge_widths = get_edge_widths_by_type(G_proj)
        crop_xlim, crop_ylim = get_crop_limits(G_proj, fig)
        
        ox.plot_graph(
            G_proj, ax=ax, bgcolor=theme['bg'],
            node_size=0,
            edge_color=edge_colors,
            edge_linewidth=edge_widths,
            show=False, close=False
        )
        ax.set_aspect('equal', adjustable='box')
        ax.set_xlim(crop_xlim)
        ax.set_ylim(crop_ylim)
        
        # Gradients
        create_gradient_fade(ax, theme['gradient_color'], location='bottom', zorder=10)
        create_gradient_fade(ax, theme['gradient_color'], location='top', zorder=10)
        
        send_progress(job_id, 'render', 90, 'Adding typography...')
        
        # Typography
        if FONTS:
            font_sub = FontProperties(fname=FONTS['light'], size=22)
            font_coords = FontProperties(fname=FONTS['regular'], size=14)
            font_attr = FontProperties(fname=FONTS['light'], size=8)
        else:
            font_sub = FontProperties(family='monospace', weight='normal', size=22)
            font_coords = FontProperties(family='monospace', size=14)
            font_attr = FontProperties(family='monospace', size=8)
        
        spaced_city = "  ".join(list(city.upper()))
        
        # Adjust font size for long names
        city_char_count = len(city)
        if city_char_count > 10:
            scale_factor = 10 / city_char_count
            adjusted_font_size = max(60 * scale_factor, 24)
        else:
            adjusted_font_size = 60
        
        if FONTS:
            font_main_adjusted = FontProperties(fname=FONTS['bold'], size=adjusted_font_size)
        else:
            font_main_adjusted = FontProperties(family='monospace', weight='bold', size=adjusted_font_size)
        
        ax.text(0.5, 0.14, spaced_city, transform=ax.transAxes,
                color=theme['text'], ha='center', fontproperties=font_main_adjusted, zorder=11)
        
        if country:
            ax.text(0.5, 0.10, country.upper(), transform=ax.transAxes,
                    color=theme['text'], ha='center', fontproperties=font_sub, zorder=11)
        
        lat_hemisphere = "N" if lat >= 0 else "S"
        lon_hemisphere = "E" if lon >= 0 else "W"
        coords_text = f"{abs(lat):.4f}° {lat_hemisphere} / {abs(lon):.4f}° {lon_hemisphere}"
        
        ax.text(0.5, 0.07, coords_text, transform=ax.transAxes,
                color=theme['text'], alpha=0.7, ha='center', fontproperties=font_coords, zorder=11)
        
        ax.plot([0.4, 0.6], [0.125, 0.125], transform=ax.transAxes, 
                color=theme['text'], linewidth=1, zorder=11)
        
        ax.text(0.98, 0.02, "© OpenStreetMap contributors", transform=ax.transAxes,
                color=theme['text'], alpha=0.5, ha='right', va='bottom', 
                fontproperties=font_attr, zorder=11)
        
        # Step 6: Save to temp directory (90-100%)
        send_progress(job_id, 'save', 95, 'Preparing download...')
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        city_slug = city.lower().replace(' ', '_').replace(',', '')
        filename = f"{city_slug}_{theme_name}_{timestamp}.{output_format}"
        output_path = str(TEMP_DIR / filename)
        
        save_kwargs = dict(facecolor=theme["bg"], bbox_inches="tight", pad_inches=0.05)
        if output_format == "png":
            save_kwargs["dpi"] = 300
        
        plt.savefig(output_path, format=output_format, **save_kwargs)
        plt.close()
        
        # Store temp path for download
        temp_downloads[job_id] = output_path
        
        download_url = url_for('download_temp', job_id=job_id, _external=False)
        send_complete(job_id, filename, download_url)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        send_error(job_id, f'Error: {str(e)}')

# ==================== Routes ====================
@app.route('/')
def index():
    themes = get_themes_with_details()
    return render_template('index.html', themes=themes, sizes=list(POSTER_SIZES.keys()))

@app.route('/api/search')
def search_address():
    """Search for addresses using Nominatim."""
    query = request.args.get('q', '')
    if not query or len(query) < 3:
        return jsonify([])
    
    try:
        wait_for_rate_limit()
        geolocator = Nominatim(user_agent=NOMINATIM_USER_AGENT, timeout=10)
        locations = geolocator.geocode(query, exactly_one=False, limit=5, addressdetails=True)
        
        results = []
        if locations:
            for loc in locations:
                address = getattr(loc, 'raw', {}).get('address', {})
                city = address.get('city') or address.get('town') or address.get('village') or address.get('municipality', '')
                country = address.get('country', '')
                
                results.append({
                    'display_name': loc.address,
                    'lat': loc.latitude,
                    'lon': loc.longitude,
                    'city': city,
                    'country': country
                })
        
        return jsonify(results)
    except Exception as e:
                logging.error("Search error: %s", e)
                return jsonify({'error': 'Search failed'}), 500

@app.route('/api/themes')
def get_themes():
    """Get all available themes."""
    return jsonify(get_themes_with_details())

@app.route('/api/generate', methods=['POST'])
def generate():
    """Start poster generation."""
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Invalid JSON payload'}), 400

    if not data.get('city'):
        return jsonify({'error': 'City name is required'}), 400

    try:
        lat_raw = data.get('lat')
        lon_raw = data.get('lon')
        lat = float(lat_raw)
        lon = float(lon_raw)
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid coordinates'}), 400

    if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lon <= 180.0):
        return jsonify({'error': 'Coordinates out of range'}), 400

    distance_raw = data.get('distance', 10000)
    try:
        distance_val = float(distance_raw)
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid distance'}), 400
    distance_val = max(1000, min(distance_val, MAX_DISTANCE_METERS))

    theme_name = data.get('theme', 'feature_based')
    if not THEME_NAME_PATTERN.match(str(theme_name)):
        return jsonify({'error': 'Invalid theme name'}), 400

    data.update({
        'lat': lat,
        'lon': lon,
        'distance': distance_val,
        'theme': theme_name,
    })

    job_id = str(uuid.uuid4())
    progress_store.create(job_id)

    # Start generation in background thread
    thread = threading.Thread(target=generate_poster, args=(job_id, data), daemon=False)
    thread.start()

    return jsonify({'job_id': job_id})

@app.route('/api/progress/<job_id>')
def progress(job_id: str):
    """Stream progress updates via Server-Sent Events."""
    def generate_events() -> Generator[str, None, None]:
        q = progress_store.get_queue(job_id)
        if q is None:
            yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
            return

        while True:
            try:
                update = q.get(timeout=60)
                yield f"data: {json.dumps(update)}\n\n"
                
                if update.get('step') in ['complete', 'error']:
                    # Clean up queue after completion
                    progress_store.delete(job_id)
                    break
            except queue.Empty:
                # Send keepalive
                progress_store.touch(job_id)
                yield f"data: {json.dumps({'keepalive': True})}\n\n"
    
    return Response(generate_events(), mimetype='text/event-stream')

@app.route('/download/temp/<job_id>')
def download_temp(job_id):
    """Download newly generated poster from temp directory."""
    if job_id not in temp_downloads:
        return "Download nicht gefunden oder abgelaufen", 404
    
    filepath = temp_downloads[job_id]
    if not os.path.exists(filepath):
        return "Datei nicht gefunden", 404
    
    filename = os.path.basename(filepath)
    
    # Send file and schedule cleanup
    response = send_file(filepath, as_attachment=True, download_name=filename)
    
    # Clean up after a delay (keep for 1 hour for multiple downloads)
    def cleanup_later():
        time.sleep(3600)  # 1 hour
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
            if job_id in temp_downloads:
                del temp_downloads[job_id]
        except:
            pass
    
    cleanup_thread = threading.Thread(target=cleanup_later, daemon=True)
    cleanup_thread.start()
    
    return response

@app.route('/download/<filename>')
def download_poster(filename):
    """Download example poster from posters directory."""
    safe_file = safe_path(POSTERS_PATH, filename)
    if safe_file and safe_file.exists():
        return send_file(str(safe_file), as_attachment=True)
    return "Invalid filename", 400

@app.route('/preview/<filename>')
def preview_poster(filename):
    """Preview poster image (for gallery thumbnails)."""
    safe_file = safe_path(POSTERS_PATH, filename)
    if safe_file and safe_file.exists():
        mimetype = 'image/png'
        if filename.endswith('.svg'):
            mimetype = 'image/svg+xml'
        elif filename.endswith('.pdf'):
            mimetype = 'application/pdf'
        return send_file(str(safe_file), mimetype=mimetype)
    return "Invalid filename", 400

@app.route('/api/posters')
def list_posters():
    """List all generated posters."""
    posters = []
    if os.path.exists(POSTERS_DIR):
        for f in sorted(os.listdir(POSTERS_DIR), reverse=True):
            if f.endswith(('.png', '.svg', '.pdf')):
                filepath = os.path.join(POSTERS_DIR, f)
                stat = os.stat(filepath)
                posters.append({
                    'filename': f,
                    'size': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'download_url': url_for('download_poster', filename=f),
                    'preview_url': url_for('preview_poster', filename=f)
                })
    return jsonify(posters)

if __name__ == '__main__':
    print("=" * 50)
    print("Map Poster Web UI")
    print("=" * 50)
    debug_env = os.getenv("FLASK_DEBUG", "false").lower()
    debug_mode = debug_env in ("1", "true", "yes", "on", "debug")
    print(f"Starting server at http://localhost:5000 (debug={debug_mode})")
    app.run(debug=debug_mode, host='0.0.0.0', port=5000, threaded=True)

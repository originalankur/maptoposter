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
import time
import threading
import queue
from datetime import datetime
from pathlib import Path
from hashlib import md5
import pickle
from typing import Optional, Generator
import uuid

app = Flask(__name__)
CORS(app)

# ==================== Configuration ====================
CACHE_DIR_PATH = os.environ.get("CACHE_DIR", "cache")
CACHE_DIR = Path(CACHE_DIR_PATH)
CACHE_DIR.mkdir(exist_ok=True)

THEMES_DIR = "themes"
FONTS_DIR = "fonts"
POSTERS_DIR = "posters"

# Create posters directory if it doesn't exist
Path(POSTERS_DIR).mkdir(exist_ok=True)

# Store for progress updates (job_id -> queue)
progress_queues: dict[str, queue.Queue] = {}

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
        print(f"Cache error: {e}")

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

# ==================== Progress Updates ====================
def send_progress(job_id: str, step: str, progress: int, message: str):
    """Send progress update to client."""
    if job_id in progress_queues:
        progress_queues[job_id].put({
            'step': step,
            'progress': progress,
            'message': message
        })

def send_complete(job_id: str, filename: str, download_url: str):
    """Send completion message to client."""
    if job_id in progress_queues:
        progress_queues[job_id].put({
            'step': 'complete',
            'progress': 100,
            'message': 'Poster erfolgreich erstellt!',
            'filename': filename,
            'download_url': download_url
        })

def send_error(job_id: str, error_message: str):
    """Send error message to client."""
    if job_id in progress_queues:
        progress_queues[job_id].put({
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
        send_progress(job_id, 'fetch_streets', 20, 'Straßennetz aus Cache geladen')
        return cached

    try:
        G = ox.graph_from_point(point, dist=dist, dist_type='bbox', network_type='all')
        time.sleep(0.5)
        cache_set(graph_key, G)
        return G
    except Exception as e:
        print(f"Error fetching graph: {e}")
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
        data = ox.features_from_point(point, tags=tags, dist=dist)
        time.sleep(0.3)
        cache_set(features_key, data)
        return data
    except Exception as e:
        print(f"Error fetching {name}: {e}")
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
        send_progress(job_id, 'fetch_streets', 5, 'Lade Straßennetz...')
        G = fetch_graph(point, dist, job_id)
        if G is None:
            send_error(job_id, 'Straßennetz konnte nicht geladen werden')
            return
        send_progress(job_id, 'fetch_streets', 20, 'Straßennetz geladen')
        
        # Step 2: Fetch Water Features (20-35%)
        send_progress(job_id, 'fetch_water', 25, 'Lade Gewässer...')
        water = fetch_features(point, dist, {'natural': 'water', 'waterway': 'riverbank'}, 'water',
                              job_id, 'fetch_water', 35, 'Gewässer geladen')
        
        # Step 3: Fetch Parks (35-50%)
        send_progress(job_id, 'fetch_parks', 40, 'Lade Parks...')
        parks = fetch_features(point, dist, {'leisure': 'park', 'landuse': 'grass'}, 'parks',
                              job_id, 'fetch_parks', 50, 'Parks geladen')
        
        # Step 4: Fetch Buildings if enabled (50-65%)
        buildings = None
        if include_buildings:
            send_progress(job_id, 'fetch_buildings', 55, 'Lade Gebäude...')
            buildings = fetch_features(point, dist, {'building': True}, 'buildings',
                                       job_id, 'fetch_buildings', 65, 'Gebäude geladen')
        else:
            send_progress(job_id, 'fetch_buildings', 65, 'Gebäude übersprungen')
        
        # Step 5: Render Map (65-90%)
        send_progress(job_id, 'render', 70, 'Erstelle Karte...')
        
        fig, ax = plt.subplots(figsize=fig_size, facecolor=theme['bg'])
        ax.set_facecolor(theme['bg'])
        ax.set_position((0.0, 0.0, 1.0, 1.0))
        
        # Project graph
        G_proj = ox.project_graph(G)
        
        send_progress(job_id, 'render', 75, 'Zeichne Layer...')
        
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
        
        send_progress(job_id, 'render', 80, 'Zeichne Gebäude...')
        
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
        
        send_progress(job_id, 'render', 85, 'Zeichne Straßen...')
        
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
        
        send_progress(job_id, 'render', 90, 'Füge Text hinzu...')
        
        # Typography
        if FONTS:
            font_main = FontProperties(fname=FONTS['bold'], size=60)
            font_sub = FontProperties(fname=FONTS['light'], size=22)
            font_coords = FontProperties(fname=FONTS['regular'], size=14)
            font_attr = FontProperties(fname=FONTS['light'], size=8)
        else:
            font_main = FontProperties(family='monospace', weight='bold', size=60)
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
        
        coords_text = f"{lat:.4f}° N / {lon:.4f}° E" if lat >= 0 else f"{abs(lat):.4f}° S / {lon:.4f}° E"
        if lon < 0:
            coords_text = coords_text.replace("E", "W")
        
        ax.text(0.5, 0.07, coords_text, transform=ax.transAxes,
                color=theme['text'], alpha=0.7, ha='center', fontproperties=font_coords, zorder=11)
        
        ax.plot([0.4, 0.6], [0.125, 0.125], transform=ax.transAxes, 
                color=theme['text'], linewidth=1, zorder=11)
        
        ax.text(0.98, 0.02, "© OpenStreetMap contributors", transform=ax.transAxes,
                color=theme['text'], alpha=0.5, ha='right', va='bottom', 
                fontproperties=font_attr, zorder=11)
        
        # Step 6: Save (90-100%)
        send_progress(job_id, 'save', 95, 'Speichere Poster...')
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        city_slug = city.lower().replace(' ', '_').replace(',', '')
        filename = f"{city_slug}_{theme_name}_{timestamp}.{output_format}"
        output_path = os.path.join(POSTERS_DIR, filename)
        
        save_kwargs = dict(facecolor=theme["bg"], bbox_inches="tight", pad_inches=0.05)
        if output_format == "png":
            save_kwargs["dpi"] = 300
        
        plt.savefig(output_path, format=output_format, **save_kwargs)
        plt.close()
        
        download_url = url_for('download_poster', filename=filename, _external=False)
        send_complete(job_id, filename, download_url)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        send_error(job_id, f'Fehler: {str(e)}')

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
        geolocator = Nominatim(user_agent="maptoposter_web", timeout=10)
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
        return jsonify({'error': str(e)}), 500

@app.route('/api/themes')
def get_themes():
    """Get all available themes."""
    return jsonify(get_themes_with_details())

@app.route('/api/generate', methods=['POST'])
def generate():
    """Start poster generation."""
    data = request.json
    
    if not data.get('lat') or not data.get('lon'):
        return jsonify({'error': 'Koordinaten fehlen'}), 400
    if not data.get('city'):
        return jsonify({'error': 'Stadtname fehlt'}), 400
    
    job_id = str(uuid.uuid4())
    progress_queues[job_id] = queue.Queue()
    
    # Start generation in background thread
    thread = threading.Thread(target=generate_poster, args=(job_id, data))
    thread.daemon = True
    thread.start()
    
    return jsonify({'job_id': job_id})

@app.route('/api/progress/<job_id>')
def progress(job_id: str):
    """Stream progress updates via Server-Sent Events."""
    def generate_events() -> Generator[str, None, None]:
        if job_id not in progress_queues:
            yield f"data: {json.dumps({'error': 'Job nicht gefunden'})}\n\n"
            return
        
        q = progress_queues[job_id]
        while True:
            try:
                update = q.get(timeout=60)
                yield f"data: {json.dumps(update)}\n\n"
                
                if update.get('step') in ['complete', 'error']:
                    # Clean up queue after completion
                    del progress_queues[job_id]
                    break
            except queue.Empty:
                # Send keepalive
                yield f"data: {json.dumps({'keepalive': True})}\n\n"
    
    return Response(generate_events(), mimetype='text/event-stream')

@app.route('/download/<filename>')
def download_poster(filename):
    """Download generated poster."""
    filepath = os.path.join(POSTERS_DIR, filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    return "Datei nicht gefunden", 404

@app.route('/preview/<filename>')
def preview_poster(filename):
    """Preview poster image (for gallery thumbnails)."""
    filepath = os.path.join(POSTERS_DIR, filename)
    if os.path.exists(filepath):
        # Serve the file inline (not as download)
        mimetype = 'image/png'
        if filename.endswith('.svg'):
            mimetype = 'image/svg+xml'
        elif filename.endswith('.pdf'):
            mimetype = 'application/pdf'
        return send_file(filepath, mimetype=mimetype)
    return "Datei nicht gefunden", 404

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
    print("Starting server at http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)

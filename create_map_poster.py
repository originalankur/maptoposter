import osmnx as ox
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib import font_manager
import matplotlib.colors as mcolors
import numpy as np
from geopy.geocoders import Nominatim
from tqdm import tqdm
import time
import json
import os
from datetime import datetime
import argparse
from PIL import Image, ImageDraw, ImageFont

THEMES_DIR = "themes"
FONTS_DIR = "fonts"
POSTERS_DIR = "posters"

def load_fonts():
    """
    Load Roboto fonts from the fonts directory.
    Returns dict with font paths for different weights.
    """
    fonts = {
        'bold': os.path.join(FONTS_DIR, 'Roboto-Bold.ttf'),
        'regular': os.path.join(FONTS_DIR, 'Roboto-Regular.ttf'),
        'light': os.path.join(FONTS_DIR, 'Roboto-Light.ttf')
    }
    
    # Verify fonts exist
    for weight, path in fonts.items():
        if not os.path.exists(path):
            print(f"⚠ Font not found: {path}")
            return None
    
    return fonts

FONTS = load_fonts()

def generate_output_filename(city, theme_name, lat=None, lon=None):
    """
    Generate unique output filename with city, theme, and datetime.
    Falls back to lat_lon if city is not provided.
    """
    if not os.path.exists(POSTERS_DIR):
        os.makedirs(POSTERS_DIR)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if city:
        city_slug = city.lower().replace(' ', '_')
        filename = f"{city_slug}_{theme_name}_{timestamp}.png"
    else:
        # Use coordinates if city not provided
        filename = f"{lat:.6f}_{lon:.6f}_{theme_name}_{timestamp}.png"
    return os.path.join(POSTERS_DIR, filename)

def get_available_themes():
    """
    Scans the themes directory and returns a list of available theme names.
    """
    if not os.path.exists(THEMES_DIR):
        os.makedirs(THEMES_DIR)
        return []
    
    themes = []
    for file in sorted(os.listdir(THEMES_DIR)):
        if file.endswith('.json'):
            theme_name = file[:-5]  # Remove .json extension
            themes.append(theme_name)
    return themes

def load_theme(theme_name="feature_based"):
    """
    Load theme from JSON file in themes directory.
    """
    theme_file = os.path.join(THEMES_DIR, f"{theme_name}.json")
    
    if not os.path.exists(theme_file):
        print(f"⚠ Theme file '{theme_file}' not found. Using default feature_based theme.")
        # Fallback to embedded default theme
        return {
            "name": "Feature-Based Shading",
            "bg": "#FFFFFF",
            "text": "#000000",
            "gradient_color": "#FFFFFF",
            "water": "#C0C0C0",
            "parks": "#F0F0F0",
            "road_motorway": "#0A0A0A",
            "road_primary": "#1A1A1A",
            "road_secondary": "#2A2A2A",
            "road_tertiary": "#3A3A3A",
            "road_residential": "#4A4A4A",
            "road_default": "#3A3A3A"
        }
    
    with open(theme_file, 'r') as f:
        theme = json.load(f)
        print(f"✓ Loaded theme: {theme.get('name', theme_name)}")
        if 'description' in theme:
            print(f"  {theme['description']}")
        return theme

# Load theme (can be changed via command line or input)
THEME = None  # Will be loaded later

def create_gradient_fade(ax, color, location='bottom', zorder=10):
    """
    Creates a fade effect at the top or bottom of the map.
    """
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

def get_edge_colors_by_type(G):
    """
    Assigns colors to edges based on road type hierarchy.
    Returns a list of colors corresponding to each edge in the graph.
    """
    edge_colors = []
    
    for u, v, data in G.edges(data=True):
        # Get the highway type (can be a list or string)
        highway = data.get('highway', 'unclassified')
        
        # Handle list of highway types (take the first one)
        if isinstance(highway, list):
            highway = highway[0] if highway else 'unclassified'
        
        # Assign color based on road type
        if highway in ['motorway', 'motorway_link']:
            color = THEME['road_motorway']
        elif highway in ['trunk', 'trunk_link', 'primary', 'primary_link']:
            color = THEME['road_primary']
        elif highway in ['secondary', 'secondary_link']:
            color = THEME['road_secondary']
        elif highway in ['tertiary', 'tertiary_link']:
            color = THEME['road_tertiary']
        elif highway in ['residential', 'living_street', 'unclassified']:
            color = THEME['road_residential']
        else:
            color = THEME['road_default']
        
        edge_colors.append(color)
    
    return edge_colors

def get_edge_widths_by_type(G):
    """
    Assigns line widths to edges based on road type.
    Major roads get thicker lines.
    """
    edge_widths = []
    
    for u, v, data in G.edges(data=True):
        highway = data.get('highway', 'unclassified')
        
        if isinstance(highway, list):
            highway = highway[0] if highway else 'unclassified'
        
        # Assign width based on road importance
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

def format_coords(lat: float, lon: float, decimals: int = 6) -> str:
    """
    Format coordinates with cardinal directions.
    Example: 32.760275°N · 97.256112°W
    """
    ns = "N" if lat >= 0 else "S"
    ew = "E" if lon >= 0 else "W"
    return f"{abs(lat):.{decimals}f}°{ns} · {abs(lon):.{decimals}f}°{ew}"

def _get_font_path() -> str:
    """Get DejaVu Sans font path from matplotlib (reliable across platforms)."""
    return font_manager.findfont("DejaVu Sans")

def _fit_font(draw: ImageDraw.ImageDraw, text: str, font_path: str, start_size: int, max_width: int) -> ImageFont.FreeTypeFont:
    """Auto-shrink font size until text fits within max_width."""
    size = start_size
    while size > 8:
        font = ImageFont.truetype(font_path, size=size)
        bbox = draw.textbbox((0, 0), text, font=font, stroke_width=2)
        w = bbox[2] - bbox[0]
        if w <= max_width:
            return font
        size -= 1
    return ImageFont.truetype(font_path, size=8)

def overlay_labels_png(png_path: str, label1: str | None, label2: str | None, label3: str | None, text_color: str):
    """
    Overlay 3-line label block at the bottom of the PNG image.
    Auto-fits font sizes to 92% of image width.
    """
    labels = [x for x in [label1, label2, label3] if x and x.strip()]
    if not labels:
        return

    img = Image.open(png_path).convert("RGBA")
    draw = ImageDraw.Draw(img)
    font_path = _get_font_path()

    W, H = img.size
    max_w = int(W * 0.92)
    bottom_margin = int(H * 0.06)

    # Starting sizes scale with image height
    title_sz = int(H * 0.055)
    sub_sz = int(H * 0.028)
    coord_sz = int(H * 0.024)

    sizes = [title_sz, sub_sz, coord_sz][:len(labels)]
    fonts = []
    for t, sz in zip(labels, sizes):
        fonts.append(_fit_font(draw, t, font_path, sz, max_w))

    # Measure total height with spacing
    line_gap = int(H * 0.010)
    heights = []
    for t, f in zip(labels, fonts):
        bbox = draw.textbbox((0, 0), t, font=f, stroke_width=2)
        heights.append(bbox[3] - bbox[1])
    total_h = sum(heights) + line_gap * (len(labels) - 1)

    y = H - bottom_margin - total_h
    stroke_fill = "#000000" if text_color.upper() != "#000000" else "#FFFFFF"

    for t, f, h in zip(labels, fonts, heights):
        bbox = draw.textbbox((0, 0), t, font=f, stroke_width=2)
        w = bbox[2] - bbox[0]
        x = (W - w) // 2
        draw.text((x, y), t, font=f, fill=text_color, stroke_width=2, stroke_fill=stroke_fill)
        y += h + line_gap

    img.convert("RGB").save(png_path, quality=95)

def get_coordinates(city, country):
    """
    Fetches coordinates for a given city and country using geopy.
    Includes rate limiting to be respectful to the geocoding service.
    Now includes retry logic and longer timeout for robustness.
    """
    print("Looking up coordinates...")
    geolocator = Nominatim(user_agent="maptoposter", timeout=10)
    
    # Add a small delay to respect Nominatim's usage policy
    time.sleep(1)
    
    for attempt in range(3):
        try:
            location = geolocator.geocode(f"{city}, {country}")
            if location:
                print(f"✓ Found: {location.address}")
                print(f"✓ Coordinates: {location.latitude}, {location.longitude}")
                return (location.latitude, location.longitude)
            else:
                if attempt == 2:
                    raise ValueError(f"Could not find coordinates for {city}, {country}")
        except Exception as e:
            if attempt == 2:
                raise
            time.sleep(1.0)
    
    raise ValueError(f"Could not find coordinates for {city}, {country}")

def create_poster(city, country, point, dist, output_file, args=None):
    location_str = f"{city}, {country}" if city and country else f"{point[0]:.6f}, {point[1]:.6f}"
    print(f"\nGenerating map for {location_str}...")
    
    # Progress bar for data fetching
    with tqdm(total=3, desc="Fetching map data", unit="step", bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}') as pbar:
        # 1. Fetch Street Network
        pbar.set_description("Downloading street network")
        G = ox.graph_from_point(point, dist=dist, dist_type='bbox', network_type='all')
        pbar.update(1)
        time.sleep(0.5)  # Rate limit between requests
        
        # 2. Fetch Water Features
        pbar.set_description("Downloading water features")
        try:
            water = ox.features_from_point(point, tags={'natural': 'water', 'waterway': 'riverbank'}, dist=dist)
        except:
            water = None
        pbar.update(1)
        time.sleep(0.3)
        
        # 3. Fetch Parks
        pbar.set_description("Downloading parks/green spaces")
        try:
            parks = ox.features_from_point(point, tags={'leisure': 'park', 'landuse': 'grass'}, dist=dist)
        except:
            parks = None
        pbar.update(1)
    
    print("✓ All data downloaded successfully!")
    
    # 2. Setup Plot
    print("Rendering map...")
    fig, ax = plt.subplots(figsize=(12, 16), facecolor=THEME['bg'])
    ax.set_facecolor(THEME['bg'])
    ax.set_position([0, 0, 1, 1])
    
    # 3. Plot Layers
    # Layer 1: Polygons
    if water is not None and not water.empty:
        water.plot(ax=ax, facecolor=THEME['water'], edgecolor='none', zorder=1)
    if parks is not None and not parks.empty:
        parks.plot(ax=ax, facecolor=THEME['parks'], edgecolor='none', zorder=2)
    
    # Layer 2: Roads with hierarchy coloring
    print("Applying road hierarchy colors...")
    edge_colors = get_edge_colors_by_type(G)
    edge_widths = get_edge_widths_by_type(G)
    
    ox.plot_graph(
        G, ax=ax, bgcolor=THEME['bg'],
        node_size=0,
        edge_color=edge_colors,
        edge_linewidth=edge_widths,
        show=False, close=False
    )
    
    # Layer 3: Gradients (Top and Bottom)
    create_gradient_fade(ax, THEME['gradient_color'], location='bottom', zorder=10)
    create_gradient_fade(ax, THEME['gradient_color'], location='top', zorder=10)
    
    # 4. Typography using Roboto font
    if FONTS:
        font_main = FontProperties(fname=FONTS['bold'], size=60)
        font_top = FontProperties(fname=FONTS['bold'], size=40)
        font_sub = FontProperties(fname=FONTS['light'], size=22)
        font_coords = FontProperties(fname=FONTS['regular'], size=14)
    else:
        # Fallback to system fonts
        font_main = FontProperties(family='monospace', weight='bold', size=60)
        font_top = FontProperties(family='monospace', weight='bold', size=40)
        font_sub = FontProperties(family='monospace', weight='normal', size=22)
        font_coords = FontProperties(family='monospace', size=14)
    
    # --- BOTTOM TEXT ---
    # Only draw default city/country text if no custom labels provided
    if not (args and (args.label1 or args.label2 or args.label3)):
        if city and country:
            if args and args.no_letterspacing:
                city_text = city.upper()
            else:
                city_text = "  ".join(list(city.upper()))
            
            ax.text(0.5, 0.14, city_text, transform=ax.transAxes,
                    color=THEME['text'], ha='center', fontproperties=font_main, zorder=11)
            
            ax.text(0.5, 0.10, country.upper(), transform=ax.transAxes,
                    color=THEME['text'], ha='center', fontproperties=font_sub, zorder=11)
        
        lat, lon = point
        coords = f"{lat:.4f}° N / {lon:.4f}° E" if lat >= 0 else f"{abs(lat):.4f}° S / {lon:.4f}° E"
        if lon < 0:
            coords = coords.replace("E", "W")
        
        ax.text(0.5, 0.07, coords, transform=ax.transAxes,
                color=THEME['text'], alpha=0.7, ha='center', fontproperties=font_coords, zorder=11)
        
        if city and country:
            ax.plot([0.4, 0.6], [0.125, 0.125], transform=ax.transAxes, 
                    color=THEME['text'], linewidth=1, zorder=11)

    # --- ATTRIBUTION (bottom right) ---
    if FONTS:
        font_attr = FontProperties(fname=FONTS['light'], size=8)
    else:
        font_attr = FontProperties(family='monospace', size=8)
    
    ax.text(0.98, 0.02, "© OpenStreetMap contributors", transform=ax.transAxes,
            color=THEME['text'], alpha=0.5, ha='right', va='bottom', 
            fontproperties=font_attr, zorder=11)

    # 5. Save
    print(f"Saving to {output_file}...")
    plt.savefig(output_file, dpi=300, facecolor=THEME['bg'])
    plt.close()
    print(f"✓ Done! Poster saved as {output_file}")
    
    # 6. Overlay custom labels if provided
    if args and (args.label1 or args.label2 or args.label3):
        label3 = args.label3
        if label3 is None and args.lat is not None and args.lon is not None:
            label3 = format_coords(args.lat, args.lon)
        overlay_labels_png(output_file, args.label1, args.label2, label3, THEME.get("text", "#000000"))
        print(f"✓ Custom labels overlaid")

def print_examples():
    """Print usage examples."""
    print("""
City Map Poster Generator
=========================

Usage:
  python create_map_poster.py --city <city> --country <country> [options]

Examples:
  # Iconic grid patterns
  python create_map_poster.py -c "New York" -C "USA" -t noir -d 12000           # Manhattan grid
  python create_map_poster.py -c "Barcelona" -C "Spain" -t warm_beige -d 8000   # Eixample district grid
  
  # Waterfront & canals
  python create_map_poster.py -c "Venice" -C "Italy" -t blueprint -d 4000       # Canal network
  python create_map_poster.py -c "Amsterdam" -C "Netherlands" -t ocean -d 6000  # Concentric canals
  python create_map_poster.py -c "Dubai" -C "UAE" -t midnight_blue -d 15000     # Palm & coastline
  
  # Radial patterns
  python create_map_poster.py -c "Paris" -C "France" -t pastel_dream -d 10000   # Haussmann boulevards
  python create_map_poster.py -c "Moscow" -C "Russia" -t noir -d 12000          # Ring roads
  
  # Organic old cities
  python create_map_poster.py -c "Tokyo" -C "Japan" -t japanese_ink -d 15000    # Dense organic streets
  python create_map_poster.py -c "Marrakech" -C "Morocco" -t terracotta -d 5000 # Medina maze
  python create_map_poster.py -c "Rome" -C "Italy" -t warm_beige -d 8000        # Ancient street layout
  
  # Coastal cities
  python create_map_poster.py -c "San Francisco" -C "USA" -t sunset -d 10000    # Peninsula grid
  python create_map_poster.py -c "Sydney" -C "Australia" -t ocean -d 12000      # Harbor city
  python create_map_poster.py -c "Mumbai" -C "India" -t contrast_zones -d 18000 # Coastal peninsula
  
  # River cities
  python create_map_poster.py -c "London" -C "UK" -t noir -d 15000              # Thames curves
  python create_map_poster.py -c "Budapest" -C "Hungary" -t copper_patina -d 8000  # Danube split
  
  # List themes
  python create_map_poster.py --list-themes

Options:
  --city, -c        City name (required)
  --country, -C     Country name (required)
  --theme, -t       Theme name (default: feature_based)
  --distance, -d    Map radius in meters (default: 29000)
  --list-themes     List all available themes

Distance guide:
  4000-6000m   Small/dense cities (Venice, Amsterdam old center)
  8000-12000m  Medium cities, focused downtown (Paris, Barcelona)
  15000-20000m Large metros, full city view (Tokyo, Mumbai)

Available themes can be found in the 'themes/' directory.
Generated posters are saved to 'posters/' directory.
""")

def list_themes():
    """List all available themes with descriptions."""
    available_themes = get_available_themes()
    if not available_themes:
        print("No themes found in 'themes/' directory.")
        return
    
    print("\nAvailable Themes:")
    print("-" * 60)
    for theme_name in available_themes:
        theme_path = os.path.join(THEMES_DIR, f"{theme_name}.json")
        try:
            with open(theme_path, 'r') as f:
                theme_data = json.load(f)
                display_name = theme_data.get('name', theme_name)
                description = theme_data.get('description', '')
        except:
            display_name = theme_name
            description = ''
        print(f"  {theme_name}")
        print(f"    {display_name}")
        if description:
            print(f"    {description}")
        print()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate beautiful map posters for any city",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python create_map_poster.py --city "New York" --country "USA"
  python create_map_poster.py --city Tokyo --country Japan --theme midnight_blue
  python create_map_poster.py --city Paris --country France --theme noir --distance 15000
  python create_map_poster.py --list-themes
        """
    )
    
    parser.add_argument('--city', '-c', type=str, help='City name')
    parser.add_argument('--country', '-C', type=str, help='Country name')
    parser.add_argument('--theme', '-t', type=str, default='feature_based', help='Theme name (default: feature_based)')
    parser.add_argument('--distance', '-d', type=int, default=29000, help='Map radius in meters (default: 29000)')
    parser.add_argument('--list-themes', action='store_true', help='List all available themes')
    parser.add_argument('--lat', type=float, help='Latitude (skip geocoding)')
    parser.add_argument('--lon', type=float, help='Longitude (skip geocoding)')
    parser.add_argument('--label1', type=str, help='Bottom label line 1 (title)')
    parser.add_argument('--label2', type=str, help='Bottom label line 2 (subtitle)')
    parser.add_argument('--label3', type=str, help='Bottom label line 3 (coords). If omitted and lat/lon present, it will be auto-formatted.')
    parser.add_argument('--no-letterspacing', action='store_true', help='Disable letter-spaced default city/country text')
    
    args = parser.parse_args()
    
    # If no arguments provided, show examples
    if len(os.sys.argv) == 1:
        print_examples()
        os.sys.exit(0)
    
    # List themes if requested
    if args.list_themes:
        list_themes()
        os.sys.exit(0)
    
    # Validate required arguments
    if not (args.lat is not None and args.lon is not None) and (not args.city or not args.country):
        print("Error: Either --city and --country, or --lat and --lon are required.\n")
        print_examples()
        os.sys.exit(1)
    
    # Validate theme exists
    available_themes = get_available_themes()
    if args.theme not in available_themes:
        print(f"Error: Theme '{args.theme}' not found.")
        print(f"Available themes: {', '.join(available_themes)}")
        os.sys.exit(1)
    
    print("=" * 50)
    print("City Map Poster Generator")
    print("=" * 50)
    
    # Load theme
    THEME = load_theme(args.theme)
    
    # Get coordinates and generate poster
    try:
        if args.lat is not None and args.lon is not None:
            coords = (args.lat, args.lon)
            print(f"✓ Using provided coordinates: {args.lat}, {args.lon}")
        else:
            coords = get_coordinates(args.city, args.country)
        output_file = generate_output_filename(args.city, args.theme, args.lat, args.lon)
        create_poster(args.city, args.country, coords, args.distance, output_file, args)
        
        print("\n" + "=" * 50)
        print("✓ Poster generation complete!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        os.sys.exit(1)

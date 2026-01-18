import osmnx as ox
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import matplotlib.colors as mcolors
import numpy as np
from geopy.geocoders import Nominatim
from tqdm import tqdm
import time
import json
import os
from datetime import datetime
import argparse

THEMES_DIR = "themes"
FONTS_DIR = "fonts"
POSTERS_DIR = "posters"

def load_fonts():
    """Load Roboto fonts from the fonts directory."""
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

def generate_output_filename(city, theme_name):
    if not os.path.exists(POSTERS_DIR):
        os.makedirs(POSTERS_DIR)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    city_slug = city.lower().replace(' ', '_')
    filename = f"{city_slug}_{theme_name}_{timestamp}.png"
    return os.path.join(POSTERS_DIR, filename)

def get_available_themes():
    if not os.path.exists(THEMES_DIR):
        os.makedirs(THEMES_DIR)
        return []
    themes = []
    for file in sorted(os.listdir(THEMES_DIR)):
        if file.endswith('.json'):
            themes.append(file[:-5])
    return themes

def load_theme(theme_name="feature_based"):
    theme_file = os.path.join(THEMES_DIR, f"{theme_name}.json")
    if not os.path.exists(theme_file):
        return {
            "name": "Default", "bg": "#FFFFFF", "text": "#000000", "gradient_color": "#FFFFFF",
            "water": "#C0C0C0", "parks": "#F0F0F0", "road_motorway": "#0A0A0A",
            "road_primary": "#1A1A1A", "road_secondary": "#2A2A2A", "road_tertiary": "#3A3A3A",
            "road_residential": "#4A4A4A", "road_default": "#3A3A3A"
        }
    with open(theme_file, 'r') as f:
        return json.load(f)

# --- INTERACTIVE INPUT FUNCTION ---
def get_multiple_highlights():
    print("\n--- Interactive Highlight Setup ---")
    try:
        count_input = input("How many different types of areas would you like to highlight? (e.g., 2): ").strip()
        count = int(count_input) if count_input else 0
    except ValueError:
        return []

    highlight_configs = []
    for i in range(count):
        print(f"\n--- Setting up Highlight #{i+1} ---")
        key = input(f"  Enter OSM tag Key (e.g., 'amenity'): ").strip()
        value = input(f"  Enter Value for '{key}' (e.g., 'hospital'): ").strip()
        color = input(f"  Enter HEX color for this (default #FF4500): ").strip() or "#FF4500"
        
        highlight_configs.append({
            'key': key,
            'value': value,
            'color': color
        })
    return highlight_configs

THEME = None

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
        extent_y_start = 0; extent_y_end = 0.25
    else:
        my_colors[:, 3] = np.linspace(0, 1, 256)
        extent_y_start = 0.75; extent_y_end = 1.0

    custom_cmap = mcolors.ListedColormap(my_colors)
    xlim, ylim = ax.get_xlim(), ax.get_ylim()
    y_range = ylim[1] - ylim[0]
    y_bottom = ylim[0] + y_range * extent_y_start
    y_top = ylim[0] + y_range * extent_y_end
    
    ax.imshow(gradient, extent=[xlim[0], xlim[1], y_bottom, y_top], 
              aspect='auto', cmap=custom_cmap, zorder=zorder, origin='lower')

def get_edge_colors_by_type(G):
    edge_colors = []
    for u, v, data in G.edges(data=True):
        highway = data.get('highway', 'unclassified')
        if isinstance(highway, list): highway = highway[0] if highway else 'unclassified'
        
        if highway in ['motorway', 'motorway_link']: color = THEME['road_motorway']
        elif highway in ['trunk', 'trunk_link', 'primary', 'primary_link']: color = THEME['road_primary']
        elif highway in ['secondary', 'secondary_link']: color = THEME['road_secondary']
        elif highway in ['tertiary', 'tertiary_link']: color = THEME['road_tertiary']
        elif highway in ['residential', 'living_street', 'unclassified']: color = THEME['road_residential']
        else: color = THEME['road_default']
        edge_colors.append(color)
    return edge_colors

def get_edge_widths_by_type(G):
    edge_widths = []
    for u, v, data in G.edges(data=True):
        highway = data.get('highway', 'unclassified')
        if isinstance(highway, list): highway = highway[0] if highway else 'unclassified'
        
        if highway in ['motorway', 'motorway_link']: width = 2
        elif highway in ['trunk', 'trunk_link', 'primary', 'primary_link']: width = 1.8
        elif highway in ['secondary', 'secondary_link']: width = 1
        elif highway in ['tertiary', 'tertiary_link']: width = 0.4
        else: width = 0.2
        edge_widths.append(width)
    return edge_widths

def get_coordinates(city, country):
    print("Looking up coordinates...")
    geolocator = Nominatim(user_agent="city_map_poster")
    time.sleep(1)
    location = geolocator.geocode(f"{city}, {country}")
    if location:
        print(f"✓ Found: {location.address}")
        return (location.latitude, location.longitude)
    else:
        raise ValueError(f"Could not find coordinates for {city}, {country}")

def create_poster(city, country, point, dist, output_file, highlight_configs=[]):
    print(f"\nGenerating map for {city}, {country}...")
    
    # Increase total steps by the number of custom highlights
    total_steps = 4 + len(highlight_configs)
    
    with tqdm(total=total_steps, desc="Fetching map data", unit="step") as pbar:
        # 1. Street Network
        pbar.set_description("Downloading streets")
        G = ox.graph_from_point(point, dist=dist, dist_type='bbox', network_type='all')
        pbar.update(1); time.sleep(0.5)
        
        # 2. Water & Parks
        pbar.set_description("Downloading nature")
        try: water = ox.features_from_point(point, tags={'natural': 'water', 'waterway': 'riverbank'}, dist=dist)
        except: water = None
        try: parks = ox.features_from_point(point, tags={'leisure': 'park', 'landuse': 'grass'}, dist=dist)
        except: parks = None
        pbar.update(1); time.sleep(0.5)

        # 3. Buildings
        pbar.set_description("Downloading buildings")
        try: buildings = ox.features_from_point(point, tags={'building': True}, dist=dist)
        except: buildings = None
        pbar.update(1); time.sleep(0.5)

        # 4. CUSTOM HIGHLIGHTS LOOP
        active_highlights = []
        for config in highlight_configs:
            k, v, c = config['key'], config['value'], config['color']
            pbar.set_description(f"Downloading: {k}={v}")
            try:
                gdf = ox.features_from_point(point, tags={k: v}, dist=dist)
                if not gdf.empty:
                    active_highlights.append({'gdf': gdf, 'color': c, 'key': k, 'val': v})
            except: pass
            pbar.update(1); time.sleep(0.5)
    
    print("✓ All data downloaded successfully!")
    print("Rendering map...")
    
    fig, ax = plt.subplots(figsize=(12, 16), facecolor=THEME['bg'])
    ax.set_facecolor(THEME['bg'])
    ax.set_position([0, 0, 1, 1])
    
    # --- LAYER 1: BASE POLYGONS (Water/Parks) ---
    if water is not None and not water.empty:
        w_polys = water[water.geom_type.isin(['Polygon', 'MultiPolygon'])]
        if not w_polys.empty:
            w_polys.plot(ax=ax, facecolor=THEME['water'], edgecolor='none', zorder=1)
    if parks is not None and not parks.empty:
        p_polys = parks[parks.geom_type.isin(['Polygon', 'MultiPolygon'])]
        if not p_polys.empty:
            p_polys.plot(ax=ax, facecolor=THEME['parks'], edgecolor='none', zorder=2)

    # --- LAYER 2: HIGHLIGHT FILLS (Bottom of sandwich) ---
    # Z-Order 2.5: Above parks, Below buildings
    for item in active_highlights:
        gdf = item['gdf']
        h_polys = gdf[gdf.geom_type.isin(['Polygon', 'MultiPolygon'])]
        if not h_polys.empty:
            h_polys.plot(ax=ax, facecolor=item['color'], alpha=0.1, edgecolor='none', zorder=2.5)

    # --- LAYER 3: BUILDINGS (Blueprint Style) ---
    # Z-Order 3: "Inside" the highlights, but above the fill
    if buildings is not None and not buildings.empty:
        b_polys = buildings[buildings.geom_type.isin(['Polygon', 'MultiPolygon'])]
        if not b_polys.empty:
            # White, very transparent (0.08) for subtle look
            b_polys.plot(ax=ax, facecolor='#FFFFFF', alpha=0.08, edgecolor='none', zorder=3)

    # --- LAYER 4: ROADS ---
    edge_colors = get_edge_colors_by_type(G)
    edge_widths = get_edge_widths_by_type(G)
    ox.plot_graph(G, ax=ax, bgcolor=THEME['bg'], node_size=0, 
                  edge_color=edge_colors, edge_linewidth=edge_widths, show=False, close=False)

    # --- LAYER 5: HIGHLIGHT CONTOURS (Top of sandwich) ---
    # Z-Order 15: Above everything including roads
    for item in active_highlights:
        gdf = item['gdf']
        h_polys = gdf[gdf.geom_type.isin(['Polygon', 'MultiPolygon'])]
        if not h_polys.empty:
            # Strong outline
            h_polys.plot(ax=ax, facecolor='none', edgecolor=item['color'], linewidth=0.8, alpha=0.8, zorder=15)
            print(f"✓ Drawn highlight: {item['key']}={item['val']}")

    # --- OVERLAYS ---
    create_gradient_fade(ax, THEME['gradient_color'], location='bottom', zorder=16)
    create_gradient_fade(ax, THEME['gradient_color'], location='top', zorder=16)
    
    # Typography
    if FONTS:
        font_main = FontProperties(fname=FONTS['bold'], size=60)
        font_top = FontProperties(fname=FONTS['bold'], size=40)
        font_sub = FontProperties(fname=FONTS['light'], size=22)
        font_coords = FontProperties(fname=FONTS['regular'], size=14)
    else:
        font_main = FontProperties(family='monospace', weight='bold', size=60)
        font_top = FontProperties(family='monospace', weight='bold', size=40)
        font_sub = FontProperties(family='monospace', weight='normal', size=22)
        font_coords = FontProperties(family='monospace', size=14)
    
    spaced_city = "  ".join(list(city.upper()))
    ax.text(0.5, 0.14, spaced_city, transform=ax.transAxes, color=THEME['text'], ha='center', fontproperties=font_main, zorder=17)
    ax.text(0.5, 0.10, country.upper(), transform=ax.transAxes, color=THEME['text'], ha='center', fontproperties=font_sub, zorder=17)
    
    lat, lon = point
    coords = f"{lat:.4f}° N / {lon:.4f}° E" if lat >= 0 else f"{abs(lat):.4f}° S / {lon:.4f}° E"
    if lon < 0: coords = coords.replace("E", "W")
    
    ax.text(0.5, 0.07, coords, transform=ax.transAxes, color=THEME['text'], alpha=0.7, ha='center', fontproperties=font_coords, zorder=17)
    ax.plot([0.4, 0.6], [0.125, 0.125], transform=ax.transAxes, color=THEME['text'], linewidth=1, zorder=17)
    
    if FONTS: font_attr = FontProperties(fname=FONTS['light'], size=8)
    else: font_attr = FontProperties(family='monospace', size=8)
    ax.text(0.98, 0.02, "© OpenStreetMap contributors", transform=ax.transAxes, color=THEME['text'], alpha=0.5, ha='right', va='bottom', fontproperties=font_attr, zorder=17)

    print(f"Saving to {output_file}...")
    plt.savefig(output_file, dpi=300, facecolor=THEME['bg'])
    plt.close()
    print(f"✓ Done! Poster saved as {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate beautiful map posters")
    parser.add_argument('--city', '-c', type=str, help='City name')
    parser.add_argument('--country', '-C', type=str, help='Country name')
    parser.add_argument('--theme', '-t', type=str, default='feature_based', help='Theme name')
    parser.add_argument('--distance', '-d', type=int, default=29000, help='Map radius in meters')
    parser.add_argument('--list-themes', action='store_true', help='List available themes')
    
    args = parser.parse_args()
    
    if args.list_themes:
        list_themes(); os.sys.exit(0)
    
    if not args.city or not args.country:
        print("Usage: python create_map_poster.py --city <city> --country <country>")
        os.sys.exit(1)
    
    THEME = load_theme(args.theme)
    
    # 1. Ask for Interactive Highlights
    configs = get_multiple_highlights()

    try:
        coords = get_coordinates(args.city, args.country)
        output_file = generate_output_filename(args.city, args.theme)
        create_poster(args.city, args.country, coords, args.distance, output_file, highlight_configs=configs)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback; traceback.print_exc()

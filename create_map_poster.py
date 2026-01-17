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
from fastkml import kml
from shapely.geometry import LineString, MultiLineString, Point, Polygon, MultiPolygon
from shapely.ops import unary_union
import geopandas as gpd

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

def generate_output_filename(city, theme_name):
    """
    Generate unique output filename with city, theme, and datetime.
    """
    if not os.path.exists(POSTERS_DIR):
        os.makedirs(POSTERS_DIR)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    city_slug = city.lower().replace(' ', '_')
    filename = f"{city_slug}_{theme_name}_{timestamp}.png"
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

def get_coordinates(city, country):
    """
    Fetches coordinates for a given city and country using geopy.
    Includes rate limiting to be respectful to the geocoding service.
    """
    print("Looking up coordinates...")
    geolocator = Nominatim(user_agent="city_map_poster")

    # Add a small delay to respect Nominatim's usage policy
    time.sleep(1)

    location = geolocator.geocode(f"{city}, {country}")

    if location:
        print(f"✓ Found: {location.address}")
        print(f"✓ Coordinates: {location.latitude}, {location.longitude}")
        return (location.latitude, location.longitude)
    else:
        raise ValueError(f"Could not find coordinates for {city}, {country}")


def parse_kml_file(kml_path):
    """
    Parse a KML file and extract route geometries and metadata.
    Returns a dict with route geometry, name, and other metadata.
    """
    print(f"Parsing KML file: {kml_path}")

    if not os.path.exists(kml_path):
        raise FileNotFoundError(f"KML file not found: {kml_path}")

    with open(kml_path, 'rb') as f:
        kml_content = f.read()

    k = kml.KML.from_string(kml_content)

    # Collect all geometries and names
    lines = []
    points = []
    polygons = []
    name = None
    description = None

    def extract_features(element):
        """Recursively extract features from KML elements."""
        nonlocal name, description

        # Try to get name/description from document or folder
        if hasattr(element, 'name') and element.name and not name:
            name = element.name
        if hasattr(element, 'description') and element.description and not description:
            description = element.description

        # Check if this element has geometry (fastkml 1.x uses kml_geometry)
        geom = None
        if hasattr(element, 'kml_geometry') and element.kml_geometry is not None:
            # fastkml 1.x style
            geom = element.kml_geometry.geometry
        elif hasattr(element, 'geometry') and element.geometry is not None:
            # Older fastkml or direct geometry access
            geom = element.geometry

        if geom is not None:
            # Use geom_type for duck typing (works with both shapely and pygeoif)
            geom_type = getattr(geom, 'geom_type', type(geom).__name__)
            if geom_type in ('LineString', 'MultiLineString'):
                # Convert to shapely if needed
                if not isinstance(geom, (LineString, MultiLineString)):
                    from shapely import wkt
                    geom = wkt.loads(str(geom))
                lines.append(geom)
            elif geom_type == 'Point':
                if not isinstance(geom, Point):
                    from shapely import wkt
                    geom = wkt.loads(str(geom))
                points.append(geom)
            elif geom_type in ('Polygon', 'MultiPolygon'):
                if not isinstance(geom, (Polygon, MultiPolygon)):
                    from shapely import wkt
                    geom = wkt.loads(str(geom))
                polygons.append(geom)

        # Recursively process features
        if hasattr(element, 'features'):
            for feature in element.features:
                extract_features(feature)

    # Extract all features from KML
    extract_features(k)

    # Combine all line geometries into a single MultiLineString
    route_geometry = None
    if lines:
        if len(lines) == 1:
            route_geometry = lines[0]
        else:
            # Flatten any MultiLineStrings and combine
            all_lines = []
            for line in lines:
                if isinstance(line, MultiLineString):
                    all_lines.extend(line.geoms)
                else:
                    all_lines.append(line)
            route_geometry = MultiLineString(all_lines)

    if route_geometry is None:
        raise ValueError("No route (line geometry) found in KML file")

    print(f"✓ Found route with {len(lines)} segment(s)")
    if name:
        print(f"✓ Route name: {name}")

    return {
        'geometry': route_geometry,
        'name': name,
        'description': description,
        'points': points,
        'polygons': polygons
    }


def get_kml_bounds(kml_data, padding=0.1):
    """
    Calculate the bounding box and center point from KML geometry.
    Returns (center_point, distance) suitable for OSMnx queries.

    padding: fraction to add as padding around the route (0.1 = 10%)
    """
    geometry = kml_data['geometry']

    # Get the bounding box
    minx, miny, maxx, maxy = geometry.bounds

    # Add padding
    width = maxx - minx
    height = maxy - miny
    minx -= width * padding
    maxx += width * padding
    miny -= height * padding
    maxy += height * padding

    # Calculate center point
    center_lat = (miny + maxy) / 2
    center_lon = (minx + maxx) / 2

    # Calculate distance (approximate meters from degrees)
    # Using Haversine approximation at the latitude
    import math
    lat_rad = math.radians(center_lat)

    # Approximate degrees to meters conversion
    meters_per_degree_lat = 111320  # roughly constant
    meters_per_degree_lon = 111320 * math.cos(lat_rad)

    # Calculate the distance needed for the bounding box
    lat_range = (maxy - miny) * meters_per_degree_lat
    lon_range = (maxx - minx) * meters_per_degree_lon

    # Use the larger dimension as the distance (for bbox query)
    distance = max(lat_range, lon_range) / 2

    # Ensure minimum distance
    distance = max(distance, 2000)

    print(f"✓ Route bounds: ({miny:.4f}, {minx:.4f}) to ({maxy:.4f}, {maxx:.4f})")
    print(f"✓ Center point: ({center_lat:.4f}, {center_lon:.4f})")
    print(f"✓ Map distance: {distance:.0f}m")

    return (center_lat, center_lon), distance, (minx, miny, maxx, maxy)


def calculate_route_stats(kml_data):
    """
    Calculate statistics about the route (distance, elevation gain if available).
    """
    geometry = kml_data['geometry']

    # Calculate approximate distance in km
    from shapely.ops import transform
    import pyproj

    # Create a projection for accurate distance calculation
    # Use the center of the geometry to determine the UTM zone
    centroid = geometry.centroid

    # Simple approximation using geodesic distance
    total_distance = 0

    def get_coords(geom):
        if isinstance(geom, LineString):
            return [geom.coords]
        elif isinstance(geom, MultiLineString):
            return [line.coords for line in geom.geoms]
        return []

    for coords_list in get_coords(geometry):
        coords = list(coords_list)
        for i in range(len(coords) - 1):
            lon1, lat1 = coords[i][0], coords[i][1]
            lon2, lat2 = coords[i + 1][0], coords[i + 1][1]

            # Haversine formula
            import math
            R = 6371  # Earth's radius in km
            lat1_rad, lat2_rad = math.radians(lat1), math.radians(lat2)
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)

            a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            total_distance += R * c

    return {
        'distance_km': total_distance,
        'distance_mi': total_distance * 0.621371
    }

def create_poster(city, country, point, dist, output_file, kml_data=None, route_color=None, route_width=None, show_distance=False):
    """
    Create a map poster. If kml_data is provided, renders the route on top of the map.

    Args:
        city: City name for the poster
        country: Country name for the poster
        point: (lat, lon) center point
        dist: Distance in meters for the map extent
        output_file: Output file path
        kml_data: Optional dict from parse_kml_file() with route geometry
        route_color: Optional color override for the route (default from theme)
        route_width: Optional width override for the route (default: 3.0)
        show_distance: Whether to show route distance on the poster
    """
    if kml_data:
        route_name = kml_data.get('name', city)
        print(f"\nGenerating race map for {route_name}...")
    else:
        print(f"\nGenerating map for {city}, {country}...")
    
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

    # Layer 2.5: KML Route overlay (if provided)
    if kml_data is not None:
        print("Rendering route overlay...")
        route_geom = kml_data['geometry']

        # Get route color from theme or use override
        if route_color is None:
            route_color = THEME.get('route', '#FF4136')  # Default to bright red

        # Get route width or use default
        if route_width is None:
            route_width = THEME.get('route_width', 3.0)

        # Create a GeoDataFrame for the route
        route_gdf = gpd.GeoDataFrame(geometry=[route_geom], crs="EPSG:4326")

        # Plot route outline (slightly wider, for contrast)
        outline_color = THEME.get('route_outline', THEME['bg'])
        route_gdf.plot(ax=ax, color=outline_color, linewidth=route_width + 2, zorder=4)

        # Plot the main route
        route_gdf.plot(ax=ax, color=route_color, linewidth=route_width, zorder=5)

        # Add start/finish markers if we have point data
        if kml_data.get('points'):
            for i, pt in enumerate(kml_data['points'][:2]):  # Only first 2 points
                marker = 'o' if i == 0 else 's'  # Circle for start, square for finish
                ax.plot(pt.x, pt.y, marker=marker, color=route_color,
                       markersize=10, markeredgecolor=outline_color,
                       markeredgewidth=2, zorder=6)
        else:
            # Mark start and finish from route geometry
            if isinstance(route_geom, LineString):
                coords = list(route_geom.coords)
            else:
                # MultiLineString - get first and last coords
                all_coords = []
                for line in route_geom.geoms:
                    all_coords.extend(list(line.coords))
                coords = all_coords

            if coords:
                # Start marker (circle)
                start_x, start_y = coords[0][0], coords[0][1]
                ax.plot(start_x, start_y, 'o', color=route_color,
                       markersize=12, markeredgecolor=outline_color,
                       markeredgewidth=2, zorder=6)

                # Finish marker (square) - only if different from start
                end_x, end_y = coords[-1][0], coords[-1][1]
                if abs(end_x - start_x) > 0.0001 or abs(end_y - start_y) > 0.0001:
                    ax.plot(end_x, end_y, 's', color=route_color,
                           markersize=12, markeredgecolor=outline_color,
                           markeredgewidth=2, zorder=6)

    # Layer 3: Gradients (Top and Bottom)
    create_gradient_fade(ax, THEME['gradient_color'], location='bottom', zorder=10)
    create_gradient_fade(ax, THEME['gradient_color'], location='top', zorder=10)
    
    # 4. Typography using Roboto font
    if FONTS:
        font_main = FontProperties(fname=FONTS['bold'], size=60)
        font_top = FontProperties(fname=FONTS['bold'], size=40)
        font_sub = FontProperties(fname=FONTS['light'], size=22)
        font_coords = FontProperties(fname=FONTS['regular'], size=14)
        font_distance = FontProperties(fname=FONTS['bold'], size=18)
    else:
        # Fallback to system fonts
        font_main = FontProperties(family='monospace', weight='bold', size=60)
        font_top = FontProperties(family='monospace', weight='bold', size=40)
        font_sub = FontProperties(family='monospace', weight='normal', size=22)
        font_coords = FontProperties(family='monospace', size=14)
        font_distance = FontProperties(family='monospace', weight='bold', size=18)

    # Determine title text based on KML data
    if kml_data and kml_data.get('name'):
        title_text = kml_data['name'].upper()
        # For race maps, use shorter spacing if name is long
        if len(title_text) > 15:
            spaced_title = " ".join(list(title_text))
            font_main = FontProperties(fname=FONTS['bold'], size=40) if FONTS else FontProperties(family='monospace', weight='bold', size=40)
        else:
            spaced_title = "  ".join(list(title_text))
    else:
        spaced_title = "  ".join(list(city.upper()))

    # --- BOTTOM TEXT ---
    ax.text(0.5, 0.14, spaced_title, transform=ax.transAxes,
            color=THEME['text'], ha='center', fontproperties=font_main, zorder=11)

    # Show location/country
    ax.text(0.5, 0.10, country.upper(), transform=ax.transAxes,
            color=THEME['text'], ha='center', fontproperties=font_sub, zorder=11)

    # Show route distance if KML data and show_distance is enabled
    if kml_data and show_distance:
        stats = calculate_route_stats(kml_data)
        distance_text = f"{stats['distance_km']:.1f} KM  /  {stats['distance_mi']:.1f} MI"
        ax.text(0.5, 0.065, distance_text, transform=ax.transAxes,
                color=THEME['text'], alpha=0.8, ha='center', fontproperties=font_distance, zorder=11)
        # Adjust coordinates position
        coord_y = 0.04
    else:
        coord_y = 0.07

    lat, lon = point
    coords = f"{lat:.4f}° N / {lon:.4f}° E" if lat >= 0 else f"{abs(lat):.4f}° S / {lon:.4f}° E"
    if lon < 0:
        coords = coords.replace("E", "W")

    ax.text(0.5, coord_y, coords, transform=ax.transAxes,
            color=THEME['text'], alpha=0.7, ha='center', fontproperties=font_coords, zorder=11)

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

def print_examples():
    """Print usage examples."""
    print("""
Map Poster Generator - City Maps & Race Routes
===============================================

Usage:
  python create_map_poster.py --city <city> --country <country> [options]
  python create_map_poster.py --kml <file.kml> --country <region> [options]

=== CITY MAP EXAMPLES ===

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
  python create_map_poster.py -c "Rome" -C "Italy" -t warm_beige -d 8000        # Ancient street layout

=== RACE MAP EXAMPLES (KML) ===

  # Basic race map from KML file
  python create_map_poster.py --kml marathon.kml -C "Massachusetts, USA" -t noir

  # Race map with distance displayed
  python create_map_poster.py --kml boston_marathon.kml -C "Boston, USA" -t midnight_blue --show-distance

  # Custom title and styling
  python create_map_poster.py --kml my_race.kml -C "California, USA" --title "Big Sur Marathon" -t sunset

  # Custom route color and width
  python create_map_poster.py --kml triathlon.kml -C "Hawaii, USA" -t noir --route-color "#00FF00" --route-width 4

  # Adjust padding around route
  python create_map_poster.py --kml ultra.kml -C "Colorado, USA" -t blueprint --padding 0.2

  # List themes
  python create_map_poster.py --list-themes

=== OPTIONS ===

City Mode:
  --city, -c        City name (required for city mode)
  --country, -C     Country/region name (required)
  --theme, -t       Theme name (default: feature_based)
  --distance, -d    Map radius in meters (default: 29000)

KML/Race Mode:
  --kml, -k         Path to KML file with route data
  --title           Custom title for the poster (overrides KML name)
  --route-color     Route line color (e.g., "#FF4136" or "red")
  --route-width     Route line width (default: 3.0)
  --show-distance   Display route distance on poster
  --padding         Padding around route as fraction (default: 0.15)

General:
  --list-themes     List all available themes

=== DISTANCE GUIDE (City Mode) ===

  4000-6000m   Small/dense cities (Venice, Amsterdam old center)
  8000-12000m  Medium cities, focused downtown (Paris, Barcelona)
  15000-20000m Large metros, full city view (Tokyo, Mumbai)

=== KML FILE TIPS ===

  - Export routes from Strava, Garmin Connect, or Google My Maps as KML
  - The route name in the KML file becomes the poster title
  - Start/finish markers are automatically added
  - Map extent is calculated from the route bounds

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
        description="Generate beautiful map posters for any city or race route",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # City maps
  python create_map_poster.py --city "New York" --country "USA"
  python create_map_poster.py --city Tokyo --country Japan --theme midnight_blue
  python create_map_poster.py --city Paris --country France --theme noir --distance 15000

  # Race maps from KML files
  python create_map_poster.py --kml marathon_route.kml --country "USA" --theme noir
  python create_map_poster.py --kml boston_marathon.kml --country "Massachusetts, USA" --theme midnight_blue --show-distance
  python create_map_poster.py --kml my_race.kml --title "Boston Marathon" --country "USA" --route-color "#FF0000"

  python create_map_poster.py --list-themes
        """
    )

    # City mode arguments
    parser.add_argument('--city', '-c', type=str, help='City name (required unless --kml is used)')
    parser.add_argument('--country', '-C', type=str, help='Country/region name (required)')
    parser.add_argument('--theme', '-t', type=str, default='feature_based', help='Theme name (default: feature_based)')
    parser.add_argument('--distance', '-d', type=int, default=None, help='Map radius in meters (auto-calculated for KML)')
    parser.add_argument('--list-themes', action='store_true', help='List all available themes')

    # KML/Race map arguments
    parser.add_argument('--kml', '-k', type=str, help='Path to KML file with race/route data')
    parser.add_argument('--title', type=str, help='Custom title for the poster (overrides KML name or city)')
    parser.add_argument('--route-color', type=str, help='Color for the route line (e.g., "#FF4136" or "red")')
    parser.add_argument('--route-width', type=float, default=None, help='Width of the route line (default: 3.0)')
    parser.add_argument('--show-distance', action='store_true', help='Show route distance on the poster')
    parser.add_argument('--padding', type=float, default=0.15, help='Padding around route as fraction (default: 0.15)')

    args = parser.parse_args()

    # If no arguments provided, show examples
    if len(os.sys.argv) == 1:
        print_examples()
        os.sys.exit(0)

    # List themes if requested
    if args.list_themes:
        list_themes()
        os.sys.exit(0)

    # Validate required arguments based on mode
    kml_mode = args.kml is not None

    if kml_mode:
        # KML mode: --kml is required, --city is optional (derived from KML name)
        if not args.country:
            print("Error: --country is required (e.g., --country 'Massachusetts, USA').\n")
            print_examples()
            os.sys.exit(1)
        if not os.path.exists(args.kml):
            print(f"Error: KML file not found: {args.kml}")
            os.sys.exit(1)
    else:
        # City mode: --city and --country are required
        if not args.city or not args.country:
            print("Error: --city and --country are required (or use --kml for race maps).\n")
            print_examples()
            os.sys.exit(1)

    # Validate theme exists
    available_themes = get_available_themes()
    if args.theme not in available_themes:
        print(f"Error: Theme '{args.theme}' not found.")
        print(f"Available themes: {', '.join(available_themes)}")
        os.sys.exit(1)
    
    print("=" * 50)
    if kml_mode:
        print("Race Map Poster Generator")
    else:
        print("City Map Poster Generator")
    print("=" * 50)

    # Load theme
    THEME = load_theme(args.theme)

    # Get coordinates and generate poster
    try:
        if kml_mode:
            # Parse KML file
            kml_data = parse_kml_file(args.kml)

            # Override name with custom title if provided
            if args.title:
                kml_data['name'] = args.title

            # Get center point and distance from KML bounds
            coords, auto_distance, bounds = get_kml_bounds(kml_data, padding=args.padding)

            # Use auto-calculated distance unless manually specified
            distance = args.distance if args.distance else int(auto_distance)

            # Use KML name or title for city name
            city_name = kml_data.get('name') or args.title or 'Race Route'

            # Generate output filename
            output_file = generate_output_filename(city_name, args.theme)

            # Calculate and display route stats
            stats = calculate_route_stats(kml_data)
            print(f"✓ Route distance: {stats['distance_km']:.2f} km ({stats['distance_mi']:.2f} mi)")

            # Create the poster with route overlay
            create_poster(
                city_name,
                args.country,
                coords,
                distance,
                output_file,
                kml_data=kml_data,
                route_color=args.route_color,
                route_width=args.route_width,
                show_distance=args.show_distance
            )
        else:
            # Standard city mode
            coords = get_coordinates(args.city, args.country)
            distance = args.distance if args.distance else 29000
            output_file = generate_output_filename(args.city, args.theme)
            create_poster(args.city, args.country, coords, distance, output_file)

        print("\n" + "=" * 50)
        print("✓ Poster generation complete!")
        print("=" * 50)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        os.sys.exit(1)

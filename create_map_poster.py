import osmnx as ox

def project_gdf_compat(gdf, to_crs=None):
    """
    Compatibility helper for OSMnx project_gdf across versions.
    Supports OSMnx 1.x (ox.project_gdf) and 2.x (ox.projection.project_gdf).
    Falls back to GeoPandas to_crs if OSMnx projection not available.
    """
    if gdf is None or getattr(gdf, "empty", False):
        return gdf
    # OSMnx 1.x
    if hasattr(ox, "project_gdf"):
        try:
            return ox.project_gdf(gdf, to_crs=to_crs) if to_crs is not None else ox.project_gdf(gdf)
        except TypeError:
            return ox.project_gdf(gdf)
    # OSMnx 2.x style
    if hasattr(ox, "projection") and hasattr(ox.projection, "project_gdf"):
        try:
            return ox.projection.project_gdf(gdf, to_crs=to_crs) if to_crs is not None else ox.projection.project_gdf(gdf)
        except TypeError:
            return ox.projection.project_gdf(gdf)
    # Fallback: just reproject via GeoPandas if possible
    return gdf.to_crs(to_crs) if to_crs is not None else gdf

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
import math
from pathlib import Path
from datetime import datetime
import argparse
from PIL import Image, ImageDraw, ImageFont
from shapely.geometry import box as shapely_box
import geopandas as gpd

# Import design system
from poster_design import (
    StylePreset,
    build_style,
    render_poster,
    parse_bbox,
    parse_format_preset,
    parse_hex_color,
    simplify_roads,
    collapse_tiers,
)

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
            # print(f"⚠ Font not found: {path}") # Suppress warning to keep CLI clean
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
    elif lat is not None and lon is not None:
        # Use coordinates if city not provided
        filename = f"{lat:.6f}_{lon:.6f}_{theme_name}_{timestamp}.png"
    else:
        filename = f"custom_area_{theme_name}_{timestamp}.png"
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
        # Fallback to embedded default theme
        return {
            "name": "Feature-Based Shading",
            "bg": "#FFFFFF",
            "text": "#000000",
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
        return theme

# Load theme (can be changed via command line or input)
THEME = None  # Will be loaded later

def format_coords(lat: float, lon: float, decimals: int = 6) -> str:
    """
    Format coordinates with cardinal directions.
    Example: 32.760275°N · 97.256112°W
    """
    ns = "N" if lat >= 0 else "S"
    ew = "E" if lon >= 0 else "W"
    return f"{abs(lat):.{decimals}f}°{ns} · {abs(lon):.{decimals}f}°{ew}"

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
    # 1. Determine Acquisition Mode & BBox
    bbox = None
    if args.bbox:
        north, south, east, west = parse_bbox(args.bbox)
        # Convert to tuple (north, south, east, west) standard
        bbox = (north, south, east, west)
    else:
        # Calculate bbox from point + distance
        # 1 deg lat ~= 111km
        lat, lon = point
        delta_lat = dist / 111000.0
        delta_lon = dist / (111000.0 * math.cos(math.radians(lat)))
        bbox = (lat + delta_lat, lat - delta_lat, lon + delta_lon, lon - delta_lon)

    # 2. Apply Margin (Expand BBox)
    if args.margin > 0:
        m_lat = args.margin / 111000.0
        m_lon = args.margin / (111000.0 * math.cos(math.radians(bbox[0]))) # approx at top
        bbox = (bbox[0] + m_lat, bbox[1] - m_lat, bbox[2] + m_lon, bbox[3] - m_lon)

    # 3. Aspect Fit
    # Target ratio
    w_in, h_in = parse_format_preset(args.format)
    target_ratio = w_in / h_in
    
    current_height_deg = bbox[0] - bbox[1]
    current_width_deg = bbox[2] - bbox[3]
    # Approximate ratio in meters (need cos(lat))
    mean_lat = (bbox[0] + bbox[1]) / 2
    aspect_factor = math.cos(math.radians(mean_lat))
    current_ratio = (current_width_deg * aspect_factor) / current_height_deg
    
    if args.aspect_fit == 'expand':
        if current_ratio > target_ratio:
            # Too wide, increase height
            new_height_deg = (current_width_deg * aspect_factor) / target_ratio
            diff = new_height_deg - current_height_deg
            bbox = (bbox[0] + diff/2, bbox[1] - diff/2, bbox[2], bbox[3])
        elif current_ratio < target_ratio:
            # Too tall, increase width
            new_width_deg = (current_height_deg * target_ratio) / aspect_factor
            diff = new_width_deg - current_width_deg
            bbox = (bbox[0], bbox[1], bbox[2] + diff/2, bbox[3] - diff/2)
    elif args.aspect_fit == 'crop':
        if current_ratio > target_ratio:
            # Too wide, shrink width
            new_width_deg = (current_height_deg * target_ratio) / aspect_factor
            diff = current_width_deg - new_width_deg
            bbox = (bbox[0], bbox[1], bbox[2] - diff/2, bbox[3] + diff/2)
        elif current_ratio < target_ratio:
            # Too tall, shrink height
            new_height_deg = (current_width_deg * aspect_factor) / target_ratio
            diff = current_height_deg - new_height_deg
            bbox = (bbox[0] - diff/2, bbox[1] + diff/2, bbox[2], bbox[3])
            
    # 4. Fetch Data
    print(f"Fetching data for bbox: {bbox}...")
    # osmnx expects (north, south, east, west)
    
    # Graphs
    # Use graph_from_bbox (note: osmnx args order is north, south, east, west)
    with tqdm(total=3, desc="Fetching map data", unit="step", bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}') as pbar:
        # OSMnx 2.0+ expects a single bbox tuple (north, south, east, west)
        G = ox.graph_from_bbox(bbox, network_type='all')
        pbar.update(1)
        
        # Features
        # Polygon for features
        poly = shapely_box(bbox[3], bbox[1], bbox[2], bbox[0]) # minx, miny, maxx, maxy
        
        try:
            water = ox.features_from_polygon(poly, tags={'natural': 'water', 'waterway': 'riverbank'})
        except:
            water = None
        pbar.update(1)
        
        try:
            parks = ox.features_from_polygon(poly, tags={'leisure': 'park', 'landuse': 'grass', 'landuse': 'recreation_ground'})
        except:
            parks = None
        pbar.update(1)
    
    # 5. Process Geometry
    print("Processing geometry...")
    G_proj = ox.project_graph(G)
    
    if water is not None and not water.empty:
        water_proj = project_gdf_compat(water, to_crs=G_proj.graph['crs'])
    else:
        water_proj = None
        
    if parks is not None and not parks.empty:
        parks_proj = project_gdf_compat(parks, to_crs=G_proj.graph['crs'])
    else:
        parks_proj = None
        
    # Get edges as GDF
    edges_proj = ox.graph_to_gdfs(G_proj, nodes=False)
    
    # Filter/Simplify
    hide_flags = {
        "hide_parking": args.hide_parking,
        "hide_service": args.hide_service,
        "hide_footpaths": args.hide_footpaths
    }
    edges_filtered = simplify_roads(edges_proj, args.detail, hide_flags)
    edges_tiered = collapse_tiers(edges_filtered, args.tiers)
    
    # 6. Build Bundle
    
    # Get projected viewing bbox
    bbox_poly = gpd.GeoSeries([shapely_box(bbox[3], bbox[1], bbox[2], bbox[0])], crs="EPSG:4326")
    bbox_proj = bbox_poly.to_crs(G_proj.graph['crs']).total_bounds # minx, miny, maxx, maxy
    
    # Rotate?
    if args.rotate != 0:
        # Simplistic rotation of geometry center
        center = ((bbox_proj[0]+bbox_proj[2])/2, (bbox_proj[1]+bbox_proj[3])/2)
        
        # Rotate edges (keep dataframe structure)
        edges_tiered['geometry'] = edges_tiered.rotate(args.rotate, origin=center)
        
        if water_proj is not None:
             water_proj['geometry'] = water_proj.rotate(args.rotate, origin=center)
             
        if parks_proj is not None:
             parks_proj['geometry'] = parks_proj.rotate(args.rotate, origin=center)
             
        # Also rotate bbox??
        # If we rotate the world, the viewport (bbox) stays fixed?
        # Or do we want to rotate the VIEWPORT?
        # Usually user wants to rotate the MAP inside the fixed rectangle.
        # This effectively means rotating the data.
        # But if we rotate the data, the parts outside the original bbox might come in.
        # Data was fetched for original bbox.
        # So we might have missing data in corners if we rotate.
        # Ideally, we should fetch a larger area if we plan to rotate.
        # For now, let's just warn or accept it.
        pass

    # Build Style
    if args.preset != 'none':
        style = build_style(args.preset, {
            "accent": args.accent,
            "texture": args.texture,
            "vignette": args.vignette,
            "linework": args.linework
        })
    else:
        # Map existing theme or defaults
        # We try to approximate the old theme structure into StylePreset
        # or just use a default preset if --theme was passed but no preset
        # It's cleaner to encourage presets.
        # But if they used -t noir, we should probably map to 'noir' preset if it matches name
        # OR create a custom style from THEME dict.
        
        # Check if theme name matches a preset name
        if args.theme in ["noir", "blueprint", "vintage"]:
            style = build_style(args.theme, {
                "accent": args.accent,
                "texture": args.texture,
                "vignette": args.vignette,
                "linework": args.linework
            })
        else:
            # Fallback to feature_based style (classic_bw approx) but using colors from THEME if possible?
            # Doing full mapping is complex. Let's default to classic_bw or nchs_premium if they want fancy.
            # Let's map "feature_based" to "classic_bw"
            style = build_style("classic_bw", {
                "accent": args.accent,
                "texture": args.texture,
                "vignette": args.vignette,
                "linework": args.linework
            })
            if THEME:
                style.bg_color = THEME.get('bg', style.bg_color)
                style.text_color = THEME.get('text', style.text_color)
                style.water_color = THEME.get('water', style.water_color)
                style.parks_color = THEME.get('parks', style.parks_color)
                style.road_colors['major'] = THEME.get('road_primary', style.road_colors['major'])
                style.road_colors['minor'] = THEME.get('road_residential', style.road_colors['minor'])

    # Determine highlight point
    highlight_point = None
    if args.highlight == 'point':
        # Project center point
        # Center of bbox (unprojected)
        center_lat = (bbox[0] + bbox[1]) / 2
        center_lon = (bbox[2] + bbox[3]) / 2
        # Project this point
        # Use transformer from graph CRS
        # Simple hack: average of projected bbox center?
        highlight_point = ((bbox_proj[0]+bbox_proj[2])/2, (bbox_proj[1]+bbox_proj[3])/2)

    # Campus GeoJSON
    campus_poly = None
    if args.campus_geojson:
        try:
            campus_gdf = gpd.read_file(args.campus_geojson)
            campus_gdf = campus_gdf.to_crs(G_proj.graph['crs'])
            campus_poly = campus_gdf.geometry.iloc[0] # Take first
            if args.rotate != 0:
                campus_poly = campus_poly.rotate(args.rotate, origin=center)
        except Exception as e:
            print(f"Warning: Could not load campus geojson: {e}")

    # Labels
    # Logic:
    # If explicit labels provided, use them.
    # If not, use city/country/coords default logic from old code, but passed as labels.
    l1, l2, l3 = args.label1, args.label2, args.label3
    
    if not (l1 or l2 or l3):
        if city and country:
            l1 = city
            l2 = country
            # Letterspacing was handled by drawing characters with spaces.
            # poster_design doesn't do that yet.
            if not args.no_letterspacing:
                l1 = "  ".join(list(city.upper()))
                l2 = country.upper()
        
        if not l3:
            # Format coords
            c_lat = (bbox[0] + bbox[1]) / 2
            c_lon = (bbox[2] + bbox[3]) / 2
            l3 = format_coords(c_lat, c_lon)

    # Bundle
    bundle = {
        "edges": edges_tiered,
        "water": water_proj,
        "parks": parks_proj,
        "campus_poly": campus_poly,
        "style": style,
        "bbox": bbox_proj,
        "config": {
            "size_inches": (w_in, h_in),
            "dpi": args.dpi,
            "show_scale": args.show_scale,
            "show_north_arrow": args.show_north_arrow,
            "detail": args.detail,
            "tiers": args.tiers
        },
        "labels": {
            "label1": l1,
            "label2": l2,
            "label3": l3,
        },
        "highlight_point": highlight_point,
        "qr_url": args.qr_url,
        "qr_label": args.qr_label
    }
    
    # 7. Render
    print(f"Rendering to {output_file}...")
    render_poster(bundle, output_file, args.out_format)

def print_examples():
    """Print usage examples."""
    print("""
City Map Poster Generator
=========================

Usage:
  python create_map_poster.py --city <city> --country <country> [options]
  python create_map_poster.py --lat <lat> --lon <lon> [options]
  python create_map_poster.py --bbox "N,S,E,W" [options]

Examples:
  # Design System (New)
  python create_map_poster.py --preset nchs_premium --bbox "32.7610,32.7597,-97.2555,-97.2568" --margin 50
  python create_map_poster.py -c "New York" -C "USA" --preset noir --format 18x24
  
  # Iconic grid patterns
  python create_map_poster.py -c "New York" -C "USA" -t noir -d 12000
  
  # List themes
  python create_map_poster.py --list-themes
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
        print(f"  {theme_name}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate beautiful map posters for any city",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--city', '-c', type=str, help='City name')
    parser.add_argument('--country', '-C', type=str, help='Country name')
    parser.add_argument('--theme', '-t', type=str, default='feature_based', help='Theme name (default: feature_based)')
    parser.add_argument('--distance', '-d', type=int, default=29000, help='Map radius in meters (default: 29000)')
    parser.add_argument('--list-themes', action='store_true', help='List all available themes')
    parser.add_argument('--lat', type=float, help='Latitude (skip geocoding)')
    parser.add_argument('--lon', type=float, help='Longitude (skip geocoding)')
    
    # Typography
    parser.add_argument('--label1', type=str, help='Bottom label line 1 (title)')
    parser.add_argument('--label2', type=str, help='Bottom label line 2 (subtitle)')
    parser.add_argument('--label3', type=str, help='Bottom label line 3 (coords)')
    parser.add_argument('--signature', type=str, help='Optional signature text')
    parser.add_argument('--no-letterspacing', action='store_true', help='Disable letter-spaced default city/country text')
    parser.add_argument('--show-scale', action='store_true', help='Show scale bar')
    parser.add_argument('--show-north-arrow', action='store_true', help='Show north arrow')

    # Extent / Framing
    parser.add_argument('--bbox', type=str, help='Bounding box "north,south,east,west"')
    parser.add_argument('--margin', type=float, default=0, help='Margin in meters')
    parser.add_argument('--rotate', type=float, default=0, help='Rotation degrees')
    parser.add_argument('--format', type=str, default='preview', help='Output format preset (preview, 18x24, 24x36, a3, a2)')
    parser.add_argument('--aspect-fit', type=str, default='expand', choices=['none', 'expand', 'crop'], help='How to fit extent to format aspect ratio')

    # Detail / Declutter
    parser.add_argument('--detail', type=str, default='standard', choices=['campus', 'standard', 'max'], help='Level of detail')
    parser.add_argument('--hide-parking', action='store_true', help='Hide parking aisles')
    parser.add_argument('--hide-service', action='store_true', help='Hide service roads')
    parser.add_argument('--hide-footpaths', action='store_true', help='Hide footpaths')
    parser.add_argument('--tiers', type=str, default='simple', choices=['simple', 'full'], help='Road tier grouping')

    # Style / Effects
    parser.add_argument('--preset', type=str, default='none', help='Design preset (classic_bw, blueprint, noir, vintage, nchs_premium)')
    parser.add_argument('--accent', type=str, help='Accent color override (#RRGGBB)')
    parser.add_argument('--texture', type=str, default='subtle', choices=['off', 'subtle', 'paper', 'grain'], help='Texture overlay')
    parser.add_argument('--vignette', type=str, default='subtle', choices=['off', 'subtle', 'medium'], help='Vignette effect')
    parser.add_argument('--linework', type=str, default='layered', choices=['flat', 'layered'], help='Linework style')

    # Extras
    parser.add_argument('--highlight', type=str, default='off', choices=['off', 'point', 'campus'], help='Highlight mode')
    parser.add_argument('--highlight-color', type=str, help='Highlight color override')
    parser.add_argument('--campus-geojson', type=str, help='Path to campus polygon GeoJSON')
    parser.add_argument('--inset', type=str, default='off', choices=['off', 'city', 'metro'], help='Add inset map')
    parser.add_argument('--qr-url', type=str, help='URL for QR code')
    parser.add_argument('--qr-label', type=str, help='Label for QR code')

    # Output
    parser.add_argument('--out', type=str, help='Output file path')
    parser.add_argument('--out-format', type=str, default='png', choices=['png', 'pdf', 'svg'], help='Output format')
    parser.add_argument('--dpi', type=int, default=300, help='Output DPI')
    
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
    # either (city AND country) OR (lat AND lon) OR (bbox)
    has_city = args.city and args.country
    has_coords = args.lat is not None and args.lon is not None
    has_bbox = args.bbox is not None
    
    if not (has_city or has_coords or has_bbox):
        print("Error: Provide location via (--city & --country), (--lat & --lon), or (--bbox).\n")
        print_examples()
        os.sys.exit(1)
    
    print("=" * 50)
    print("City Map Poster Generator")
    print("=" * 50)
    
    # Load old theme global for compatibility
    THEME = load_theme(args.theme)
    
    # Get coordinates and generate poster
    try:
        if has_bbox:
            # We skip point geocoding if bbox is explicit
            coords = (0, 0) # Dummy
            print(f"✓ Using provided bbox: {args.bbox}")
        elif has_coords:
            coords = (args.lat, args.lon)
            print(f"✓ Using provided coordinates: {args.lat}, {args.lon}")
        else:
            coords = get_coordinates(args.city, args.country)
            
        output_file = args.out
        if not output_file:
            output_file = generate_output_filename(args.city, args.preset if args.preset != 'none' else args.theme, 
                                                coords[0] if has_coords else None, 
                                                coords[1] if has_coords else None)
            # Ensure extension matches format
            if not output_file.lower().endswith(f".{args.out_format}"):
                output_file = os.path.splitext(output_file)[0] + f".{args.out_format}"

        create_poster(args.city, args.country, coords, args.distance, output_file, args)
        
        print("\n" + "=" * 50)
        print("✓ Poster generation complete!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        os.sys.exit(1)

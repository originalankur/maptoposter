#!/usr/bin/env python3
"""
Enhanced City Map Poster Generator with Transport Stations and Landmarks
Based on the original create_map_poster.py with added layers for:
- Public transport stations (Metro, MMTS, Bus terminals)
- Historic landmarks
- Modern landmarks
"""

from networkx import MultiDiGraph
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
import sys
from datetime import datetime
import argparse
import pickle
import asyncio
from typing import cast
from geopandas import GeoDataFrame
from shapely.geometry import Point


class CacheError(Exception):
    """Raised when a cache operation fails."""
    pass


THEMES_DIR = "themes"
FONTS_DIR = "fonts"
POSTERS_DIR = "posters"
CACHE_DIR = ".cache"


def _cache_path(key: str) -> str:
    safe = key.replace(os.sep, "_")
    return os.path.join(CACHE_DIR, f"{safe}.pkl")


def cache_get(key: str):
    try:
        path = _cache_path(key)
        if not os.path.exists(path):
            return None
        with open(path, "rb") as f:
            return pickle.load(f)
    except Exception as e:
        raise CacheError(f"Cache read failed: {e}")


def cache_set(key: str, value):
    try:
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)
        path = _cache_path(key)
        with open(path, "wb") as f:
            pickle.dump(value, f, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception as e:
        raise CacheError(f"Cache write failed: {e}")


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

def generate_output_filename(city, theme_name, output_format, suffix="enhanced"):
    """
    Generate unique output filename with city, theme, and datetime.
    """
    if not os.path.exists(POSTERS_DIR):
        os.makedirs(POSTERS_DIR)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    city_slug = city.lower().replace(' ', '_')
    ext = output_format.lower()
    filename = f"{city_slug}_{theme_name}_{suffix}_{timestamp}.{ext}"
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
            "road_default": "#3A3A3A",
            "transport_station": "#FFD700",
            "landmark_historic": "#FFBF00",
            "landmark_modern": "#FFFFFF"
        }
    
    with open(theme_file, 'r') as f:
        theme = json.load(f)
        # Add default values for new properties if not present
        if 'transport_station' not in theme:
            theme['transport_station'] = '#FFD700'
        if 'landmark_historic' not in theme:
            theme['landmark_historic'] = '#FFBF00'
        if 'landmark_modern' not in theme:
            theme['landmark_modern'] = '#FFFFFF'
        print(f"✓ Loaded theme: {theme.get('name', theme_name)}")
        if 'description' in theme:
            print(f"  {theme['description']}")
        return theme

# Load theme (can be changed via command line or input)
THEME = dict[str, str]()  # Will be loaded later

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
    coords = f"coords_{city.lower()}_{country.lower()}"
    cached = cache_get(coords)
    if cached:
        print(f"✓ Using cached coordinates for {city}, {country}")
        return cached

    print("Looking up coordinates...")
    geolocator = Nominatim(user_agent="city_map_poster", timeout=10)
    
    # Add a small delay to respect Nominatim's usage policy
    time.sleep(1)
    
    try:
        location = geolocator.geocode(f"{city}, {country}")
    except Exception as e:
        raise ValueError(f"Geocoding failed for {city}, {country}: {e}")

    # If geocode returned a coroutine in some environments, run it to get the result.
    if asyncio.iscoroutine(location):
        try:
            location = asyncio.run(location)
        except RuntimeError:
            # If an event loop is already running, try using it to complete the coroutine.
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Running event loop in the same thread; raise a clear error.
                raise RuntimeError("Geocoder returned a coroutine while an event loop is already running. Run this script in a synchronous environment.")
            location = loop.run_until_complete(location)
    
    if location:
        # Use getattr to safely access address (helps static analyzers)
        addr = getattr(location, "address", None)
        if addr:
            print(f"✓ Found: {addr}")
        else:
            print("✓ Found location (address not available)")
        print(f"✓ Coordinates: {location.latitude}, {location.longitude}")
        try:
            cache_set(coords, (location.latitude, location.longitude))
        except CacheError as e:
            print(e)
        return (location.latitude, location.longitude)
    else:
        raise ValueError(f"Could not find coordinates for {city}, {country}")
    
def get_crop_limits(G_proj, center_lat_lon, fig, dist):
    """
    Crop inward to preserve aspect ratio while guaranteeing
    full coverage of the requested radius.
    """
    lat, lon = center_lat_lon

    # Project center point into graph CRS
    center = (
        ox.projection.project_geometry(
            Point(lon, lat),
            crs="EPSG:4326",
            to_crs=G_proj.graph["crs"]
        )[0]
    )
    center_x, center_y = center.x, center.y

    fig_width, fig_height = fig.get_size_inches()
    aspect = fig_width / fig_height

    # Start from the *requested* radius
    half_x = dist
    half_y = dist

    # Cut inward to match aspect
    if aspect > 1:  # landscape → reduce height
        half_y = half_x / aspect
    else:           # portrait → reduce width
        half_x = half_y * aspect

    return (
        (center_x - half_x, center_x + half_x),
        (center_y - half_y, center_y + half_y),
    )


def fetch_graph(point, dist) -> MultiDiGraph | None:
    lat, lon = point
    graph = f"graph_{lat}_{lon}_{dist}"
    cached = cache_get(graph)
    if cached is not None:
        print("✓ Using cached street network")
        return cast(MultiDiGraph, cached)

    try:
        G = ox.graph_from_point(point, dist=dist, dist_type='bbox', network_type='all', truncate_by_edge=True)
        # Rate limit between requests
        time.sleep(0.5)
        try:
            cache_set(graph, G)
        except CacheError as e:
            print(e)
        return G
    except Exception as e:
        print(f"OSMnx error while fetching graph: {e}")
        return None

def fetch_features(point, dist, tags, name) -> GeoDataFrame | None:
    lat, lon = point
    tag_str = "_".join(f"{k}_{v}" for k, v in tags.items())
    features = f"{name}_{lat}_{lon}_{dist}_{tag_str}"
    cached = cache_get(features)
    if cached is not None:
        print(f"✓ Using cached {name}")
        return cast(GeoDataFrame, cached)

    try:
        data = ox.features_from_point(point, tags=tags, dist=dist)
        # Rate limit between requests
        time.sleep(0.3)
        try:
            cache_set(features, data)
        except CacheError as e:
            print(e)
        return data
    except Exception as e:
        print(f"OSMnx error while fetching {name}: {e}")
        return None


def fetch_transport_stations(point, dist) -> GeoDataFrame | None:
    """
    Fetch public transport stations: Metro, Railway, Bus terminals
    """
    lat, lon = point
    cache_key = f"transport_{lat}_{lon}_{dist}"
    cached = cache_get(cache_key)
    if cached is not None:
        print("✓ Using cached transport stations")
        return cast(GeoDataFrame, cached)
    
    try:
        # Fetch railway stations (includes Metro and MMTS)
        railway_tags = {'railway': ['station', 'halt', 'stop']}
        railway = ox.features_from_point(point, tags=railway_tags, dist=dist)
        time.sleep(0.3)
    except Exception:
        railway = None
    
    try:
        # Fetch subway/metro stations
        subway_tags = {'station': 'subway'}
        subway = ox.features_from_point(point, tags=subway_tags, dist=dist)
        time.sleep(0.3)
    except Exception:
        subway = None
    
    try:
        # Fetch bus stations (major terminals only)
        bus_tags = {'amenity': 'bus_station'}
        bus = ox.features_from_point(point, tags=bus_tags, dist=dist)
        time.sleep(0.3)
    except Exception:
        bus = None
    
    # Combine all transport data
    import pandas as pd
    dfs = [df for df in [railway, subway, bus] if df is not None and not df.empty]
    
    if dfs:
        combined = pd.concat(dfs, ignore_index=True)
        # Convert to GeoDataFrame if needed
        if not isinstance(combined, GeoDataFrame):
            combined = GeoDataFrame(combined, geometry='geometry')
        try:
            cache_set(cache_key, combined)
        except CacheError as e:
            print(e)
        return combined
    return None


def fetch_landmarks(point, dist) -> tuple[GeoDataFrame | None, GeoDataFrame | None]:
    """
    Fetch historic and modern landmarks
    Returns: (historic_landmarks, modern_landmarks)
    """
    lat, lon = point
    
    # Historic landmarks
    historic_cache = f"historic_{lat}_{lon}_{dist}"
    historic_cached = cache_get(historic_cache)
    if historic_cached is not None:
        print("✓ Using cached historic landmarks")
        historic = historic_cached
    else:
        try:
            historic_tags = {'historic': True}
            historic = ox.features_from_point(point, tags=historic_tags, dist=dist)
            time.sleep(0.3)
            try:
                cache_set(historic_cache, historic)
            except CacheError as e:
                print(e)
        except Exception:
            historic = None
    
    # Tourism attractions (monuments, attractions)
    tourism_cache = f"tourism_{lat}_{lon}_{dist}"
    tourism_cached = cache_get(tourism_cache)
    if tourism_cached is not None:
        print("✓ Using cached tourism landmarks")
        tourism = tourism_cached
    else:
        try:
            tourism_tags = {'tourism': ['attraction', 'monument', 'museum']}
            tourism = ox.features_from_point(point, tags=tourism_tags, dist=dist)
            time.sleep(0.3)
            try:
                cache_set(tourism_cache, tourism)
            except CacheError as e:
                print(e)
        except Exception:
            tourism = None
    
    # Combine historic and tourism
    import pandas as pd
    historic_dfs = [df for df in [historic, tourism] if df is not None and not df.empty]
    historic_combined = None
    if historic_dfs:
        historic_combined = pd.concat(historic_dfs, ignore_index=True)
        if not isinstance(historic_combined, GeoDataFrame):
            historic_combined = GeoDataFrame(historic_combined, geometry='geometry')
    
    return historic_combined, None  # Modern landmarks can be added later


def create_poster(city, country, point, dist, output_file, output_format, width=12, height=16, country_label=None, name_label=None, show_transport=True, show_landmarks=True):
    print(f"\nGenerating enhanced map for {city}, {country}...")
    
    # Calculate total steps based on options
    total_steps = 3  # Base: roads, water, parks
    if show_transport:
        total_steps += 1
    if show_landmarks:
        total_steps += 1
    
    # Progress bar for data fetching
    with tqdm(total=total_steps, desc="Fetching map data", unit="step", bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}') as pbar:
        # 1. Fetch Street Network
        pbar.set_description("Downloading street network")
        compensated_dist = dist * (max(height, width) / min(height, width))/4 # To compensate for viewport crop
        G = fetch_graph(point, compensated_dist)
        if G is None:
            raise RuntimeError("Failed to retrieve street network data.")
        pbar.update(1)
        
        # 2. Fetch Water Features
        pbar.set_description("Downloading water features")
        water = fetch_features(point, compensated_dist, tags={'natural': 'water', 'waterway': 'riverbank'}, name='water')
        pbar.update(1)
        
        # 3. Fetch Parks
        pbar.set_description("Downloading parks/green spaces")
        parks = fetch_features(point, compensated_dist, tags={'leisure': 'park', 'landuse': 'grass'}, name='parks')
        pbar.update(1)
        
        # 4. Fetch Transport Stations (if enabled)
        transport = None
        if show_transport:
            pbar.set_description("Downloading transport stations")
            transport = fetch_transport_stations(point, compensated_dist)
            pbar.update(1)
        
        # 5. Fetch Landmarks (if enabled)
        historic_landmarks = None
        modern_landmarks = None
        if show_landmarks:
            pbar.set_description("Downloading landmarks")
            historic_landmarks, modern_landmarks = fetch_landmarks(point, compensated_dist)
            pbar.update(1)
    
    print("✓ All data retrieved successfully!")
    
    # Count features
    transport_count = len(transport) if transport is not None and not transport.empty else 0
    historic_count = len(historic_landmarks) if historic_landmarks is not None and not historic_landmarks.empty else 0
    print(f"  Transport stations: {transport_count}")
    print(f"  Historic landmarks: {historic_count}")
    
    # 2. Setup Plot
    print("Rendering map...")
    fig, ax = plt.subplots(figsize=(width, height), facecolor=THEME['bg'])
    ax.set_facecolor(THEME['bg'])
    ax.set_position((0.0, 0.0, 1.0, 1.0))

    # Project graph to a metric CRS so distances and aspect are linear (meters)
    G_proj = ox.project_graph(G)
    
    # 3. Plot Layers
    # Layer 1: Polygons (filter to only plot polygon/multipolygon geometries, not points)
    if water is not None and not water.empty:
        # Filter to only polygon/multipolygon geometries to avoid point features showing as dots
        water_polys = water[water.geometry.type.isin(['Polygon', 'MultiPolygon'])]
        if not water_polys.empty:
            # Project water features in the same CRS as the graph
            try:
                water_polys = ox.projection.project_gdf(water_polys)
            except Exception:
                water_polys = water_polys.to_crs(G_proj.graph['crs'])
            water_polys.plot(ax=ax, facecolor=THEME['water'], edgecolor='none', zorder=1)
    
    if parks is not None and not parks.empty:
        # Filter to only polygon/multipolygon geometries to avoid point features showing as dots
        parks_polys = parks[parks.geometry.type.isin(['Polygon', 'MultiPolygon'])]
        if not parks_polys.empty:
            # Project park features in the same CRS as the graph
            try:
                parks_polys = ox.projection.project_gdf(parks_polys)
            except Exception:
                parks_polys = parks_polys.to_crs(G_proj.graph['crs'])
            parks_polys.plot(ax=ax, facecolor=THEME['parks'], edgecolor='none', zorder=2)
    
    # Layer 2: Roads with hierarchy coloring
    print("Applying road hierarchy colors...")
    edge_colors = get_edge_colors_by_type(G_proj)
    edge_widths = get_edge_widths_by_type(G_proj)

    # Determine cropping limits to maintain the poster aspect ratio
    crop_xlim, crop_ylim = get_crop_limits(G_proj, point, fig, compensated_dist)
    # Plot the projected graph and then apply the cropped limits
    ox.plot_graph(
        G_proj, ax=ax, bgcolor=THEME['bg'],
        node_size=0,
        edge_color=edge_colors,
        edge_linewidth=edge_widths,
        show=False, close=False
    )
    ax.set_aspect('equal', adjustable='box')
    ax.set_xlim(crop_xlim)
    ax.set_ylim(crop_ylim)
    
    # Layer 3: Transport Stations (Gold dots)
    if show_transport and transport is not None and not transport.empty:
        print("Plotting transport stations...")
        # Get centroids for all geometries (works for points, polygons, etc.)
        try:
            transport_proj = ox.projection.project_gdf(transport)
        except Exception:
            transport_proj = transport.to_crs(G_proj.graph['crs'])
        
        # Get centroids
        centroids = transport_proj.geometry.centroid
        x_coords = centroids.x
        y_coords = centroids.y
        
        # Plot as scatter points
        ax.scatter(x_coords, y_coords, 
                   c=THEME.get('transport_station', '#FFD700'), 
                   s=15,  # Size of dots
                   marker='o',
                   edgecolors='none',
                   alpha=0.9,
                   zorder=5)
    
    # Layer 4: Historic Landmarks (Amber dots)
    if show_landmarks and historic_landmarks is not None and not historic_landmarks.empty:
        print("Plotting historic landmarks...")
        try:
            historic_proj = ox.projection.project_gdf(historic_landmarks)
        except Exception:
            historic_proj = historic_landmarks.to_crs(G_proj.graph['crs'])
        
        # Get centroids
        centroids = historic_proj.geometry.centroid
        x_coords = centroids.x
        y_coords = centroids.y
        
        # Plot as scatter points (slightly larger than transport)
        ax.scatter(x_coords, y_coords, 
                   c=THEME.get('landmark_historic', '#FFBF00'), 
                   s=25,  # Larger size for landmarks
                   marker='D',  # Diamond shape
                   edgecolors='white',
                   linewidths=0.5,
                   alpha=0.9,
                   zorder=6)
    
    # Layer 5: Gradients (Top and Bottom)
    create_gradient_fade(ax, THEME['gradient_color'], location='bottom', zorder=10)
    create_gradient_fade(ax, THEME['gradient_color'], location='top', zorder=10)
    
    # Calculate scale factor based on poster width (reference width 12 inches)
    scale_factor = width / 12.0
    
    # Base font sizes (at 12 inches width)
    BASE_MAIN = 60
    BASE_TOP = 40
    BASE_SUB = 22
    BASE_COORDS = 14
    BASE_ATTR = 8
    
    # 4. Typography using Roboto font
    if FONTS:
        font_main = FontProperties(fname=FONTS['bold'], size=BASE_MAIN * scale_factor)
        font_top = FontProperties(fname=FONTS['bold'], size=BASE_TOP * scale_factor)
        font_sub = FontProperties(fname=FONTS['light'], size=BASE_SUB * scale_factor)
        font_coords = FontProperties(fname=FONTS['regular'], size=BASE_COORDS * scale_factor)
        font_attr = FontProperties(fname=FONTS['light'], size=BASE_ATTR * scale_factor)
    else:
        # Fallback to system fonts
        font_main = FontProperties(family='monospace', weight='bold', size=BASE_MAIN * scale_factor)
        font_top = FontProperties(family='monospace', weight='bold', size=BASE_TOP * scale_factor)
        font_sub = FontProperties(family='monospace', weight='normal', size=BASE_SUB * scale_factor)
        font_coords = FontProperties(family='monospace', size=BASE_COORDS * scale_factor)
        font_attr = FontProperties(family='monospace', size=BASE_ATTR * scale_factor)
    
    spaced_city = "  ".join(list(city.upper()))
    
    # Dynamically adjust font size based on city name length to prevent truncation
    # We use the already scaled "main" font size as the starting point.
    base_adjusted_main = BASE_MAIN * scale_factor
    city_char_count = len(city)
    
    # Heuristic: If length is > 10, start reducing.
    if city_char_count > 10:
        length_factor = 10 / city_char_count
        adjusted_font_size = max(base_adjusted_main * length_factor, 10 * scale_factor) 
    else:
        adjusted_font_size = base_adjusted_main
    
    if FONTS:
        font_main_adjusted = FontProperties(fname=FONTS['bold'], size=adjusted_font_size)
    else:
        font_main_adjusted = FontProperties(family='monospace', weight='bold', size=adjusted_font_size)

    # --- BOTTOM TEXT ---
    ax.text(0.5, 0.14, spaced_city, transform=ax.transAxes,
            color=THEME['text'], ha='center', fontproperties=font_main_adjusted, zorder=11)
    
    country_text = country_label if country_label is not None else country
    ax.text(0.5, 0.10, country_text.upper(), transform=ax.transAxes,
            color=THEME['text'], ha='center', fontproperties=font_sub, zorder=11)
    
    lat, lon = point
    coords = f"{lat:.4f}° N / {lon:.4f}° E" if lat >= 0 else f"{abs(lat):.4f}° S / {lon:.4f}° E"
    if lon < 0:
        coords = coords.replace("E", "W")
    
    ax.text(0.5, 0.07, coords, transform=ax.transAxes,
            color=THEME['text'], alpha=0.7, ha='center', fontproperties=font_coords, zorder=11)
    
    ax.plot([0.4, 0.6], [0.125, 0.125], transform=ax.transAxes, 
            color=THEME['text'], linewidth=1 * scale_factor, zorder=11)

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

    fmt = output_format.lower()
    save_kwargs = dict(facecolor=THEME["bg"], bbox_inches="tight", pad_inches=0.05,)

    # DPI matters mainly for raster formats
    if fmt == "png":
        save_kwargs["dpi"] = 300

    plt.savefig(output_file, format=fmt, **save_kwargs)

    plt.close()
    print(f"✓ Done! Poster saved as {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate enhanced map posters with transport stations and landmarks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python create_map_poster_enhanced.py --city "Hyderabad" --country "India" --theme noir_lakes
  python create_map_poster_enhanced.py --city Tokyo --country Japan --theme midnight_blue -W 16 -H 9
        """
    )
    
    parser.add_argument('--city', '-c', type=str, help='City name')
    parser.add_argument('--country', '-C', type=str, help='Country name')
    parser.add_argument('--country-label', dest='country_label', type=str, help='Override country text displayed on poster')
    parser.add_argument('--theme', '-t', type=str, default='noir_lakes', help='Theme name (default: noir_lakes)')
    parser.add_argument('--distance', '-d', type=int, default=42000, help='Map radius in meters (default: 42000)')
    parser.add_argument('--width', '-W', type=float, default=16, help='Image width in inches (default: 16)')
    parser.add_argument('--height', '-H', type=float, default=9, help='Image height in inches (default: 9)')
    parser.add_argument('--format', '-f', default='png', choices=['png', 'svg', 'pdf'], help='Output format (default: png)')
    parser.add_argument('--no-transport', action='store_true', help='Disable transport station markers')
    parser.add_argument('--no-landmarks', action='store_true', help='Disable landmark markers')
    
    args = parser.parse_args()
    
    # Validate required arguments
    if not args.city or not args.country:
        print("Error: --city and --country are required.\n")
        parser.print_help()
        sys.exit(1)
    
    print("=" * 50)
    print("Enhanced City Map Poster Generator")
    print("=" * 50)
    
    # Get coordinates and generate poster
    try:
        coords = get_coordinates(args.city, args.country)
        THEME = load_theme(args.theme)
        output_file = generate_output_filename(args.city, args.theme, args.format)
        create_poster(
            args.city, 
            args.country, 
            coords, 
            args.distance, 
            output_file, 
            args.format, 
            args.width, 
            args.height, 
            country_label=args.country_label,
            show_transport=not args.no_transport,
            show_landmarks=not args.no_landmarks
        )
        
        print("\n" + "=" * 50)
        print("✓ Poster generation complete!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

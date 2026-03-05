#!/usr/bin/env python3
"""
City Map Poster Generator

This module generates beautiful, minimalist map posters for any city in the world.
It fetches OpenStreetMap data using OSMnx, applies customizable themes, and creates
high-quality poster-ready images with roads, water features, and parks.
"""

import argparse
import asyncio
import json
import math
import os
import pickle
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import cast

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import osmnx as ox
from geopandas import GeoDataFrame
from geopy.geocoders import Nominatim
from lat_lon_parser import parse
from matplotlib.font_manager import FontProperties
from networkx import MultiDiGraph
from shapely.geometry import Point
from tqdm import tqdm

from font_management import load_fonts

# Configure osmnx to respect HTTP_PROXY / HTTPS_PROXY environment variables
# (needed for SOCKS5 proxies in corporate/school networks)
_proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
if _proxy:
    ox.settings.requests_kwargs = {"proxies": {"http": _proxy, "https": _proxy}}
ox.settings.timeout = 600          # Overpass QL server-side [timeout:N] param
ox.settings.requests_timeout = 600  # HTTP client read timeout (actual network timeout)
ox.settings.overpass_rate_limit = False  # Skip /status check — avoids hanging on status endpoint


class CacheError(Exception):
    """Raised when a cache operation fails."""


CACHE_DIR_PATH = os.environ.get("CACHE_DIR", "cache")
CACHE_DIR = Path(CACHE_DIR_PATH)
CACHE_DIR.mkdir(exist_ok=True)

THEMES_DIR = "themes"
FONTS_DIR = "fonts"
POSTERS_DIR = "posters"

FILE_ENCODING = "utf-8"

FONTS = load_fonts()


def _cache_path(key: str) -> str:
    """
    Generate a safe cache file path from a cache key.

    Args:
        key: Cache key identifier

    Returns:
        Path to cache file with .pkl extension
    """
    safe = key.replace(os.sep, "_")
    return os.path.join(CACHE_DIR, f"{safe}.pkl")


def cache_get(key: str):
    """
    Retrieve a cached object by key.

    Args:
        key: Cache key identifier

    Returns:
        Cached object if found, None otherwise

    Raises:
        CacheError: If cache read operation fails
    """
    try:
        path = _cache_path(key)
        if not os.path.exists(path):
            return None
        with open(path, "rb") as f:
            return pickle.load(f)
    except Exception as e:
        raise CacheError(f"Cache read failed: {e}") from e


def cache_set(key: str, value):
    """
    Store an object in the cache.

    Args:
        key: Cache key identifier
        value: Object to cache (must be picklable)

    Raises:
        CacheError: If cache write operation fails
    """
    try:
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)
        path = _cache_path(key)
        with open(path, "wb") as f:
            pickle.dump(value, f, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception as e:
        raise CacheError(f"Cache write failed: {e}") from e


# Font loading now handled by font_management.py module


def is_latin_script(text):
    """
    Check if text is primarily Latin script.
    Used to determine if letter-spacing should be applied to city names.

    :param text: Text to analyze
    :return: True if text is primarily Latin script, False otherwise
    """
    if not text:
        return True

    latin_count = 0
    total_alpha = 0

    for char in text:
        if char.isalpha():
            total_alpha += 1
            # Latin Unicode ranges:
            # - Basic Latin: U+0000 to U+007F
            # - Latin-1 Supplement: U+0080 to U+00FF
            # - Latin Extended-A: U+0100 to U+017F
            # - Latin Extended-B: U+0180 to U+024F
            if ord(char) < 0x250:
                latin_count += 1

    # If no alphabetic characters, default to Latin (numbers, symbols, etc.)
    if total_alpha == 0:
        return True

    # Consider it Latin if >80% of alphabetic characters are Latin
    return (latin_count / total_alpha) > 0.8


def generate_output_filename(city, theme_name, output_format):
    """
    Generate unique output filename with city, theme, and datetime.
    """
    if not os.path.exists(POSTERS_DIR):
        os.makedirs(POSTERS_DIR)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    city_slug = city.lower().replace(" ", "_")
    ext = output_format.lower()
    filename = f"{city_slug}_{theme_name}_{timestamp}.{ext}"
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
        if file.endswith(".json"):
            theme_name = file[:-5]  # Remove .json extension
            themes.append(theme_name)
    return themes


def load_theme(theme_name="terracotta"):
    """
    Load theme from JSON file in themes directory.
    """
    theme_file = os.path.join(THEMES_DIR, f"{theme_name}.json")

    if not os.path.exists(theme_file):
        print(f"⚠ Theme file '{theme_file}' not found. Using default terracotta theme.")
        # Fallback to embedded terracotta theme
        return {
            "name": "Terracotta",
            "description": "Mediterranean warmth - burnt orange and clay tones on cream",
            "bg": "#F5EDE4",
            "text": "#8B4513",
            "gradient_color": "#F5EDE4",
            "water": "#A8C4C4",
            "parks": "#E8E0D0",
            "road_motorway": "#A0522D",
            "road_primary": "#B8653A",
            "road_secondary": "#C9846A",
            "road_tertiary": "#D9A08A",
            "road_residential": "#E5C4B0",
            "road_default": "#D9A08A",
        }

    with open(theme_file, "r", encoding="utf-8-sig") as f:
        theme = json.load(f)
        print(f"✓ Loaded theme: {theme.get('name', theme_name)}")
        if "description" in theme:
            print(f"  {theme['description']}")
        return theme


# Load theme (can be changed via command line or input)
THEME = dict[str, str]()  # Will be loaded later


def create_gradient_fade(ax, color, location="bottom", zorder=10):
    """
    Creates a perfectly smooth fade effect at the top or bottom of the map.
    Uses a direct RGBA image array (no colormap quantisation) for banding-free gradients.
    """
    N = 1024  # rows in the gradient image — high enough for smooth output
    rgb = mcolors.to_rgb(color)

    # Build RGBA image: shape (N, 2, 4)
    img = np.zeros((N, 2, 4), dtype=np.float32)
    img[:, :, 0] = rgb[0]
    img[:, :, 1] = rgb[1]
    img[:, :, 2] = rgb[2]

    if location == "bottom":
        # bottom: opaque → transparent (rows 0..N-1 map to alpha 1..0)
        alpha = np.linspace(1.0, 0.0, N)
        extent_y_start = 0.0
        extent_y_end = 0.25
    else:
        # top: transparent → opaque
        alpha = np.linspace(0.0, 1.0, N)
        extent_y_start = 0.75
        extent_y_end = 1.0

    img[:, :, 3] = alpha[:, np.newaxis]

    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    y_range = ylim[1] - ylim[0]
    y_bottom = ylim[0] + y_range * extent_y_start
    y_top    = ylim[0] + y_range * extent_y_end

    ax.imshow(
        img,
        extent=[xlim[0], xlim[1], y_bottom, y_top],
        aspect="auto",
        zorder=zorder,
        origin="lower",
        interpolation="bilinear",
    )


def create_patina_texture(ax, base_color, zorder=0.05, seed=42):
    """
    Overlays an organic mottled patina / verdigris texture on the background.
    Uses Gaussian-blurred multi-frequency noise to create natural, irregular
    blotch shapes (no grid/block artefacts).

    base_color : hex/name – the colour tint of the patina patches
    """
    from scipy.ndimage import gaussian_filter

    rng = np.random.default_rng(seed)
    H, W = 768, 576  # internal texture resolution

    # Two large-scale layers only — wide sigma for broad organic blotches
    layer_huge  = gaussian_filter(rng.random((H, W)).astype(np.float32), sigma=120)
    layer_large = gaussian_filter(rng.random((H, W)).astype(np.float32), sigma=50)

    combined = layer_huge * 0.70 + layer_large * 0.30

    # Normalise to [0, 1]
    lo, hi = combined.min(), combined.max()
    combined = (combined - lo) / (hi - lo + 1e-8)

    # Threshold: only keep the top ~50% so patches are distinct, not a wash
    combined = np.clip((combined - 0.45) / 0.55, 0, 1)

    # Build RGBA image: base_color modulates the tint, alpha carries the mask
    r, g, b = mcolors.to_rgb(base_color)
    tex = np.zeros((H, W, 4), dtype=np.float32)
    tex[:, :, 0] = r
    tex[:, :, 1] = g
    tex[:, :, 2] = b
    tex[:, :, 3] = combined * 0.30   # max 30% opacity — subtle but visible

    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    ax.imshow(
        tex,
        extent=[xlim[0], xlim[1], ylim[0], ylim[1]],
        aspect="auto",
        zorder=zorder,
        origin="upper",
        interpolation="bilinear",
    )


def create_bg_gradient(ax, color_top, color_bottom, zorder=0.1):
    """
    Creates a full-canvas vertical background gradient.
    color_top is drawn at the top of the plot, color_bottom at the bottom.
    Uses a low zorder so it sits above the solid facecolor but below all map layers.
    """
    n = 2048
    # shape (n_rows, 2_cols, 4_channels); row 0 = bottom of image (origin='lower')
    t_vals = np.linspace(0.0, 1.0, n)          # 0 = bottom colour, 1 = top colour

    rgb_top = np.array(mcolors.to_rgb(color_top),  dtype=np.float32)
    rgb_bot = np.array(mcolors.to_rgb(color_bottom), dtype=np.float32)

    gradient_data = np.zeros((n, 2, 4), dtype=np.float32)
    gradient_data[:, :, :3] = (rgb_bot[None, None, :] * (1 - t_vals[:, None, None])
                                + rgb_top[None, None, :] * t_vals[:, None, None])
    gradient_data[:, :, 3] = 1.0   # fully opaque

    xlim = ax.get_xlim()
    ylim = ax.get_ylim()

    ax.imshow(
        gradient_data,
        extent=[xlim[0], xlim[1], ylim[0], ylim[1]],
        aspect="auto",
        zorder=zorder,
        origin="lower",
        interpolation="bilinear",
    )


def get_edge_colors_by_type(g):
    """
    Assigns colors to edges based on road type hierarchy.
    Returns a list of colors corresponding to each edge in the graph.
    """
    edge_colors = []

    for _u, _v, data in g.edges(data=True):
        # Get the highway type (can be a list or string)
        highway = data.get('highway', 'unclassified')

        # Handle list of highway types (take the first one)
        if isinstance(highway, list):
            highway = highway[0] if highway else 'unclassified'

        # Assign color based on road type
        if highway in ["motorway", "motorway_link"]:
            color = THEME["road_motorway"]
        elif highway in ["trunk", "trunk_link", "primary", "primary_link"]:
            color = THEME["road_primary"]
        elif highway in ["secondary", "secondary_link"]:
            color = THEME["road_secondary"]
        elif highway in ["tertiary", "tertiary_link"]:
            color = THEME["road_tertiary"]
        elif highway in ["residential", "living_street", "unclassified"]:
            color = THEME["road_residential"]
        else:
            color = THEME['road_default']

        edge_colors.append(color)

    return edge_colors


def get_edge_widths_by_type(g):
    """
    Assigns line widths to edges based on road type.
    Major roads get thicker lines.
    Multiplied by THEME['road_width_scale'] if set.
    """
    edge_widths = []
    scale = float(THEME.get("road_width_scale", 1.0))

    for _u, _v, data in g.edges(data=True):
        highway = data.get('highway', 'unclassified')

        if isinstance(highway, list):
            highway = highway[0] if highway else 'unclassified'

        # Assign width based on road importance
        if highway in ["motorway", "motorway_link"]:
            width = 1.2
        elif highway in ["trunk", "trunk_link", "primary", "primary_link"]:
            width = 1.0
        elif highway in ["secondary", "secondary_link"]:
            width = 0.8
        elif highway in ["tertiary", "tertiary_link"]:
            width = 0.6
        else:
            width = 0.4

        edge_widths.append(width * scale)

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
        raise ValueError(f"Geocoding failed for {city}, {country}: {e}") from e

    # If geocode returned a coroutine in some environments, run it to get the result.
    if asyncio.iscoroutine(location):
        try:
            location = asyncio.run(location)
        except RuntimeError as exc:
            # If an event loop is already running, try using it to complete the coroutine.
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Running event loop in the same thread; raise a clear error.
                raise RuntimeError(
                    "Geocoder returned a coroutine while an event loop is already running. "
                    "Run this script in a synchronous environment."
                ) from exc
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

    raise ValueError(f"Could not find coordinates for {city}, {country}")


def get_crop_limits(g_proj, center_lat_lon, fig, dist, text_area_frac: float = 0.05,
                    x_offset_frac: float = 0.0, y_offset_frac: float = 0.0):
    """
    Crop inward to preserve aspect ratio while guaranteeing
    full coverage of the requested radius.

    text_area_frac: fraction of figure height to compensate for bottom text block.
                   0.05 = center at y=52.5% (default, slight upward bias).
    x_offset_frac:  positive → crop window shifts LEFT → geo-centre moves RIGHT in poster.
    y_offset_frac:  positive → crop window shifts UP   → geo-centre moves DOWN  in poster.
    """
    lat, lon = center_lat_lon

    # Project center point into graph CRS
    center = (
        ox.projection.project_geometry(
            Point(lon, lat),
            crs="EPSG:4326",
            to_crs=g_proj.graph["crs"]
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
    else:  # portrait → reduce width
        half_x = half_y * aspect

    # Shift the crop window downward so the geographic centre sits at the
    # visual mid-point of the area above the bottom text block.
    # text_area_frac: negative y_shift raises centre slightly above 50%.
    # y_offset_frac:  positive y_shift pushes window upward → centre appears lower.
    # x_offset_frac:  negative x_shift slides window leftward → centre appears righter.
    y_shift = -half_y * text_area_frac + half_y * y_offset_frac
    x_shift = -half_x * x_offset_frac

    return (
        (center_x - half_x + x_shift, center_x + half_x + x_shift),
        (center_y - half_y + y_shift, center_y + half_y + y_shift),
    )


def fetch_graph(point, dist) -> MultiDiGraph | None:
    """
    Fetch street network graph from OpenStreetMap.

    Uses caching to avoid redundant downloads. Fetches all network types
    within the specified distance from the center point.

    Args:
        point: (latitude, longitude) tuple for center point
        dist: Distance in meters from center point

    Returns:
        MultiDiGraph of street network, or None if fetch fails
    """
    lat, lon = point
    graph = f"graph_{lat}_{lon}_{dist}"
    cached = cache_get(graph)
    if cached is not None:
        print("✓ Using cached street network")
        return cast(MultiDiGraph, cached)

    # Apply a hard read-timeout so slow Overpass streams don't hang forever.
    # ox.settings.requests_timeout is the actual HTTP request timeout used by osmnx.
    # ox.settings.timeout only controls the Overpass QL [timeout:N] server-side setting.
    original_requests_timeout = ox.settings.requests_timeout
    ox.settings.requests_timeout = 600  # 10 minutes max for street network
    try:
        g = ox.graph_from_point(point, dist=dist, dist_type='bbox', network_type='all', truncate_by_edge=True)
        # Rate limit between requests
        time.sleep(0.5)
        try:
            cache_set(graph, g)
        except CacheError as e:
            print(e)
        return g
    except Exception as e:
        err_str = str(e).lower()
        if any(kw in err_str for kw in ("timed out", "timeout", "read timed",
                                         "time out", "readtimeout", "connectiontimeout")):
            print(f"⚠ Street network download timed out — skipping (poster will render without roads)")
        else:
            print(f"OSMnx error while fetching graph: {e}")
        return None
    finally:
        ox.settings.requests_timeout = original_requests_timeout


def fetch_features(point, dist, tags, name, max_dist: int | None = None,
                   timeout: int | None = None) -> GeoDataFrame | None:
    """
    Fetch geographic features (water, parks, etc.) from OpenStreetMap.

    Uses caching to avoid redundant downloads. Fetches features matching
    the specified OSM tags within distance from center point.

    Args:
        point: (latitude, longitude) tuple for center point
        dist: Distance in meters from center point
        tags: Dictionary of OSM tags to filter features
        name: Name for this feature type (for caching and logging)
        timeout: Optional per-request timeout in seconds. If specified, overrides
                 the global ox.settings.timeout for this fetch only, and also
                 injects a read-timeout into requests_kwargs so that slow/hung
                 HTTP responses are aborted.  If the request times out the layer
                 is skipped gracefully.

    Returns:
        GeoDataFrame of features, or None if fetch fails
    """
    lat, lon = point
    effective_dist = min(dist, max_dist) if max_dist is not None else dist
    tag_str = "_".join(tags.keys())
    features = f"{name}_{lat}_{lon}_{effective_dist}_{tag_str}"
    cached = cache_get(features)
    if cached is not None:
        print(f"✓ Using cached {name}")
        return cast(GeoDataFrame, cached)

    # Temporarily override osmnx HTTP timeout.
    # ox.settings.requests_timeout is the actual HTTP request timeout.
    # ox.settings.timeout only sets the Overpass QL [timeout:N] server-side param.
    original_requests_timeout = ox.settings.requests_timeout
    if timeout is not None:
        ox.settings.requests_timeout = timeout

    def _do_fetch() -> GeoDataFrame:
        return ox.features_from_point(point, tags=tags, dist=effective_dist)

    try:
        for attempt in range(2):  # 2 attempts when timeout is short
            try:
                if timeout is not None:
                    # Use thread-based wall-clock timeout to cut off hung Overpass streams.
                    # shutdown(wait=False) so we don't block waiting for the background
                    # thread even after the timeout fires.
                    import concurrent.futures
                    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
                    try:
                        future = executor.submit(_do_fetch)
                        try:
                            data = future.result(timeout=timeout)
                        except concurrent.futures.TimeoutError:
                            print(f"⚠ {name} download timed out — skipping layer (poster will render without it)")
                            executor.shutdown(wait=False)
                            return None
                    finally:
                        executor.shutdown(wait=False)
                else:
                    data = _do_fetch()
                # Rate limit between requests
                time.sleep(0.3)
                try:
                    cache_set(features, data)
                except CacheError as e:
                    print(e)
                return data
            except Exception as e:
                err_str = str(e).lower()
                # Detect timeout-related errors — treat as non-retriable
                if any(kw in err_str for kw in ("timed out", "timeout", "read timed",
                                                 "time out", "readtimeout", "connectiontimeout")):
                    print(f"⚠ {name} download timed out — skipping layer (poster will render without it)")
                    return None
                if attempt < 1:
                    print(f"OSMnx retry {attempt+1}/2 for {name}: {e}")
                    time.sleep(5 * (attempt + 1))
                else:
                    print(f"OSMnx error while fetching features: {e}")
                    return None
    finally:
        # Always restore the original settings
        ox.settings.requests_timeout = original_requests_timeout
    return None


def create_poster(
    city,
    country,
    point,
    dist,
    output_file,
    output_format,
    width=12,
    height=16,
    country_label=None,
    name_label=None,
    display_city=None,
    display_country=None,
    fonts=None,
    map_x_offset=0.0,
    map_y_offset=0.0,
):
    """
    Generate a complete map poster with roads, water, parks, and typography.

    Creates a high-quality poster by fetching OSM data, rendering map layers,
    applying the current theme, and adding text labels with coordinates.

    Args:
        city: City name for display on poster
        country: Country name for display on poster
        point: (latitude, longitude) tuple for map center
        dist: Map radius in meters
        output_file: Path where poster will be saved
        output_format: File format ('png', 'svg', or 'pdf')
        width: Poster width in inches (default: 12)
        height: Poster height in inches (default: 16)
        country_label: Optional override for country text on poster
        _name_label: Optional override for city name (unused, reserved for future use)

    Raises:
        RuntimeError: If street network data cannot be retrieved
    """
    # Handle display names for i18n support
    # Priority: display_city/display_country > name_label/country_label > city/country
    display_city = display_city or name_label or city
    display_country = display_country or country_label or country

    print(f"\nGenerating map for {city}, {country}...")

    # Progress bar for data fetching
    with tqdm(
        total=3,
        desc="Fetching map data",
        unit="step",
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}",
    ) as pbar:
        # 1. Fetch Street Network
        pbar.set_description("Downloading street network")
        compensated_dist = dist * (max(height, width) / min(height, width)) / 4  # To compensate for viewport crop
        # When map is offset, shift the fetch center so the offset region is covered.
        # map_y_offset > 0 means content shifts DOWN → viewport looks NORTH → move fetch center north.
        # map_x_offset > 0 means content shifts RIGHT → viewport looks WEST → move fetch center west.
        lat_shift_m = map_y_offset * compensated_dist   # positive y_offset → look north → lat+
        lon_shift_m = -map_x_offset * compensated_dist  # positive x_offset → look west → lon-
        meters_per_deg_lat = 111320.0
        meters_per_deg_lon = 111320.0 * abs(math.cos(math.radians(point[0])))
        fetch_point = (
            point[0] + lat_shift_m / meters_per_deg_lat,
            point[1] + lon_shift_m / meters_per_deg_lon,
        )
        # Also expand radius slightly to ensure full coverage around shifted center
        offset_extra = max(abs(map_x_offset), abs(map_y_offset)) * 0.5
        fetch_dist = compensated_dist * (1 + offset_extra)
        g = fetch_graph(fetch_point, fetch_dist)
        if g is None:
            raise RuntimeError("Failed to retrieve street network data.")
        pbar.update(1)

        # 2. Fetch Water Features
        pbar.set_description("Downloading water features")
        water = fetch_features(
            fetch_point,
            fetch_dist,
            tags={"natural": ["water", "bay", "strait"], "waterway": "riverbank"},
            name="water",
            timeout=60,
        )
        pbar.update(1)

        # 3. Fetch Parks
        pbar.set_description("Downloading parks/green spaces")
        parks = fetch_features(
            fetch_point,
            fetch_dist,
            tags={"leisure": "park", "landuse": "grass"},
            name="parks",
            max_dist=4000,
            timeout=60,
        )
        pbar.update(1)


    print("✓ All data retrieved successfully!")

    # 2. Setup Plot
    print("Rendering map...")
    bg_color = THEME["bg"]
    fig, ax = plt.subplots(figsize=(width, height), facecolor=bg_color)
    ax.set_facecolor(bg_color)
    ax.set_position((0.0, 0.0, 1.0, 1.0))

    # Project graph to a metric CRS so distances and aspect are linear (meters)
    g_proj = ox.project_graph(g)

    # 3. Plot Layers
    # Layer 1: Polygons (filter to only plot polygon/multipolygon geometries, not points)
    if water is not None and not water.empty:
        # Filter to only polygon/multipolygon geometries to avoid point features showing as dots
        water_polys = water[water.geometry.type.isin(["Polygon", "MultiPolygon"])]
        if not water_polys.empty:
            # Project water features in the same CRS as the graph
            try:
                water_polys = ox.projection.project_gdf(water_polys)
            except Exception:
                water_polys = water_polys.to_crs(g_proj.graph['crs'])
            water_polys.plot(ax=ax, facecolor=THEME['water'], edgecolor='none', zorder=0.5)

    if parks is not None and not parks.empty:
        # Filter to only polygon/multipolygon geometries to avoid point features showing as dots
        parks_polys = parks[parks.geometry.type.isin(["Polygon", "MultiPolygon"])]
        if not parks_polys.empty:
            # Project park features in the same CRS as the graph
            try:
                parks_polys = ox.projection.project_gdf(parks_polys)
            except Exception:
                parks_polys = parks_polys.to_crs(g_proj.graph['crs'])
            parks_polys.plot(ax=ax, facecolor=THEME['parks'], edgecolor='none', zorder=0.8)
    # Layer 2: Roads with hierarchy coloring
    print("Applying road hierarchy colors...")
    edge_colors = get_edge_colors_by_type(g_proj)
    edge_widths = get_edge_widths_by_type(g_proj)

    # Determine cropping limits to maintain the poster aspect ratio
    crop_xlim, crop_ylim = get_crop_limits(g_proj, point, fig, compensated_dist,
                                            x_offset_frac=map_x_offset,
                                            y_offset_frac=map_y_offset)
    # Plot the projected graph and then apply the cropped limits
    ox.plot_graph(
        g_proj, ax=ax, bgcolor=bg_color,
        node_size=0,
        edge_color=edge_colors,
        edge_linewidth=edge_widths,
        show=False,
        close=False,
    )
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(crop_xlim)
    ax.set_ylim(crop_ylim)

    # Optional background gradient (triggered by bg_top + bg_bottom in theme)
    if THEME.get("bg_top") and THEME.get("bg_bottom"):
        create_bg_gradient(ax, THEME["bg_top"], THEME["bg_bottom"], zorder=0.1)

    # Optional patina / mottled texture overlay (triggered by bg_patina in theme)
    if THEME.get("bg_patina"):
        patina_color = THEME.get("bg_patina_color") or THEME.get("road_motorway") or "#40A880"
        create_patina_texture(ax, patina_color, zorder=0.08)

    # Layer 3: Gradients (Top and Bottom)
    # When bg_top/bg_bottom are set, use them for the fade so colours are consistent
    _default_fade = THEME["gradient_color"]
    fade_top_color = THEME.get("bg_top") or _default_fade
    fade_bottom_color = THEME.get("bg_bottom") or _default_fade
    create_gradient_fade(ax, fade_bottom_color, location='bottom', zorder=10)
    create_gradient_fade(ax, fade_top_color, location='top', zorder=10)

    # Calculate scale factor based on smaller dimension (reference 12 inches)
    # This ensures text scales properly for both portrait and landscape orientations
    scale_factor = min(height, width) / 12.0

    # Base font sizes (at 12 inches width)
    base_main = 60
    base_sub = 22
    base_coords = 14
    base_attr = 8

    # 4. Typography - use custom fonts if provided, otherwise use default FONTS
    active_fonts = fonts or FONTS
    if active_fonts:
        # font_main is calculated dynamically later based on length
        font_sub = FontProperties(
            fname=active_fonts["light"], size=base_sub * scale_factor
        )
        font_coords = FontProperties(
            fname=active_fonts["regular"], size=base_coords * scale_factor
        )
        font_attr = FontProperties(
            fname=active_fonts["light"], size=base_attr * scale_factor
        )
    else:
        # Fallback to system fonts
        font_sub = FontProperties(
            family="monospace", weight="normal", size=base_sub * scale_factor
        )
        font_coords = FontProperties(
            family="monospace", size=base_coords * scale_factor
        )
        font_attr = FontProperties(family="monospace", size=base_attr * scale_factor)

    # Format city name based on script type
    # Latin scripts: apply uppercase and letter spacing for aesthetic
    # Non-Latin scripts (CJK, Thai, Arabic, etc.): no spacing, preserve case structure
    if is_latin_script(display_city):
        # Latin script: uppercase with letter spacing (e.g., "P  A  R  I  S")
        spaced_city = "  ".join(list(display_city.upper()))
    else:
        # Non-Latin script: no spacing, no forced uppercase
        # For scripts like Arabic, Thai, Japanese, etc.
        spaced_city = display_city

    # Dynamically adjust font size based on city name length to prevent truncation
    # We use the already scaled "main" font size as the starting point.
    base_adjusted_main = base_main * scale_factor
    city_char_count = len(display_city)

    # Heuristic: If length is > 10, start reducing.
    if city_char_count > 10:
        length_factor = 10 / city_char_count
        adjusted_font_size = max(base_adjusted_main * length_factor, 10 * scale_factor)
    else:
        adjusted_font_size = base_adjusted_main

    if active_fonts:
        font_main_adjusted = FontProperties(
            fname=active_fonts["bold"], size=adjusted_font_size
        )
    else:
        font_main_adjusted = FontProperties(
            family="monospace", weight="bold", size=adjusted_font_size
        )

    # --- BOTTOM TEXT ---
    ax.text(
        0.5,
        0.14,
        spaced_city,
        transform=ax.transAxes,
        color=THEME["text"],
        ha="center",
        fontproperties=font_main_adjusted,
        zorder=11,
    )

    ax.text(
        0.5,
        0.10,
        display_country.upper(),
        transform=ax.transAxes,
        color=THEME["text"],
        ha="center",
        fontproperties=font_sub,
        zorder=11,
    )

    lat, lon = point
    coords = (
        f"{lat:.4f}° N / {lon:.4f}° E"
        if lat >= 0
        else f"{abs(lat):.4f}° S / {lon:.4f}° E"
    )
    if lon < 0:
        coords = coords.replace("E", "W")

    ax.text(
        0.5,
        0.07,
        coords,
        transform=ax.transAxes,
        color=THEME["text"],
        alpha=0.7,
        ha="center",
        fontproperties=font_coords,
        zorder=11,
    )

    ax.plot(
        [0.4, 0.6],
        [0.125, 0.125],
        transform=ax.transAxes,
        color=THEME["text"],
        linewidth=1 * scale_factor,
        zorder=11,
    )

    # --- ATTRIBUTION (bottom right) ---
    if FONTS:
        font_attr = FontProperties(fname=FONTS["light"], size=8)
    else:
        font_attr = FontProperties(family="monospace", size=8)

    ax.text(
        0.98,
        0.02,
        "© OpenStreetMap contributors",
        transform=ax.transAxes,
        color=THEME["text"],
        alpha=0.5,
        ha="right",
        va="bottom",
        fontproperties=font_attr,
        zorder=11,
    )

    # 5. Save
    print(f"Saving to {output_file}...")

    fmt = output_format.lower()
    save_kwargs = dict(
        facecolor=THEME["bg"],
        bbox_inches="tight",
        pad_inches=0.05,
    )

    # DPI matters mainly for raster formats
    if fmt == "png":
        save_kwargs["dpi"] = 300

    plt.savefig(output_file, format=fmt, **save_kwargs)

    plt.close()
    print(f"✓ Done! Poster saved as {output_file}")


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
  --country-label   Override country text displayed on poster
  --theme, -t       Theme name (default: terracotta)
  --all-themes      Generate posters for all themes
  --distance, -d    Map radius in meters (default: 18000)
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
            with open(theme_path, "r", encoding="utf-8-sig") as f:
                theme_data = json.load(f)
                display_name = theme_data.get('name', theme_name)
                description = theme_data.get('description', '')
        except (OSError, json.JSONDecodeError):
            display_name = theme_name
            description = ""
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
  python create_map_poster.py --city "New York" --country "USA" -l 40.776676 -73.971321 --theme neon_cyberpunk
  python create_map_poster.py --city Tokyo --country Japan --theme midnight_blue
  python create_map_poster.py --city Paris --country France --theme noir --distance 15000
  python create_map_poster.py --list-themes
        """,
    )

    parser.add_argument("--city", "-c", type=str, help="City name")
    parser.add_argument("--country", "-C", type=str, help="Country name")
    parser.add_argument(
        "--latitude",
        "-lat",
        dest="latitude",
        type=str,
        help="Override latitude center point",
    )
    parser.add_argument(
        "--longitude",
        "-long",
        dest="longitude",
        type=str,
        help="Override longitude center point",
    )
    parser.add_argument(
        "--country-label",
        dest="country_label",
        type=str,
        help="Override country text displayed on poster",
    )
    parser.add_argument(
        "--theme",
        "-t",
        type=str,
        default="terracotta",
        help="Theme name (default: terracotta)",
    )
    parser.add_argument(
        "--all-themes",
        "--All-themes",
        dest="all_themes",
        action="store_true",
        help="Generate posters for all themes",
    )
    parser.add_argument(
        "--distance",
        "-d",
        type=int,
        default=18000,
        help="Map radius in meters (default: 18000)",
    )
    parser.add_argument(
        "--width",
        "-W",
        type=float,
        default=12,
        help="Image width in inches (default: 12, max: 20 )",
    )
    parser.add_argument(
        "--height",
        "-H",
        type=float,
        default=16,
        help="Image height in inches (default: 16, max: 20)",
    )
    parser.add_argument(
        "--list-themes", action="store_true", help="List all available themes"
    )
    parser.add_argument(
        "--display-city",
        "-dc",
        type=str,
        help="Custom display name for city (for i18n support)",
    )
    parser.add_argument(
        "--display-country",
        "-dC",
        type=str,
        help="Custom display name for country (for i18n support)",
    )
    parser.add_argument(
        "--font-family",
        type=str,
        help='Google Fonts family name (e.g., "Noto Sans JP", "Open Sans"). If not specified, uses local Roboto fonts.',
    )
    parser.add_argument(
        "--format",
        "-f",
        default="png",
        choices=["png", "svg", "pdf"],
        help="Output format for the poster (default: png)",
    )
    parser.add_argument(
        "--map-x-offset",
        "-mx",
        dest="map_x_offset",
        type=float,
        default=0.0,
        help="Horizontal map offset fraction (positive → content shifts right in poster, default: 0.0)",
    )
    parser.add_argument(
        "--map-y-offset",
        "-my",
        dest="map_y_offset",
        type=float,
        default=0.0,
        help="Vertical map offset fraction (positive → content shifts down in poster, default: 0.0)",
    )

    args = parser.parse_args()

    # If no arguments provided, show examples
    if len(sys.argv) == 1:
        print_examples()
        sys.exit(0)

    # List themes if requested
    if args.list_themes:
        list_themes()
        sys.exit(0)

    # Validate required arguments
    if not args.city or not args.country:
        print("Error: --city and --country are required.\n")
        print_examples()
        sys.exit(1)

    # Enforce maximum dimensions
    if args.width > 20:
        print(
            f"⚠ Width {args.width} exceeds the maximum allowed limit of 20. It's enforced as max limit 20."
        )
        args.width = 20.0
    if args.height > 20:
        print(
            f"⚠ Height {args.height} exceeds the maximum allowed limit of 20. It's enforced as max limit 20."
        )
        args.height = 20.0

    available_themes = get_available_themes()
    if not available_themes:
        print("No themes found in 'themes/' directory.")
        sys.exit(1)

    if args.all_themes:
        themes_to_generate = available_themes
    else:
        if args.theme not in available_themes:
            print(f"Error: Theme '{args.theme}' not found.")
            print(f"Available themes: {', '.join(available_themes)}")
            sys.exit(1)
        themes_to_generate = [args.theme]

    print("=" * 50)
    print("City Map Poster Generator")
    print("=" * 50)

    # Load custom fonts if specified
    custom_fonts = None
    if args.font_family:
        custom_fonts = load_fonts(args.font_family)
        if not custom_fonts:
            print(f"⚠ Failed to load '{args.font_family}', falling back to Roboto")

    # Get coordinates and generate poster
    try:
        if args.latitude and args.longitude:
            lat = parse(args.latitude)
            lon = parse(args.longitude)
            coords = [lat, lon]
            print(f"✓ Coordinates: {', '.join([str(i) for i in coords])}")
        else:
            coords = get_coordinates(args.city, args.country)

        for theme_name in themes_to_generate:
            THEME = load_theme(theme_name)
            output_file = generate_output_filename(args.city, theme_name, args.format)
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
                display_city=args.display_city,
                display_country=args.display_country,
                fonts=custom_fonts,
                map_x_offset=args.map_x_offset,
                map_y_offset=args.map_y_offset,
            )

        print("\n" + "=" * 50)
        print("✓ Poster generation complete!")
        print("=" * 50)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

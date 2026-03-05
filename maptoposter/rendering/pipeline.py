"""
Poster rendering pipeline orchestrator.

Coordinates data fetching, figure setup, layer rendering, and file output.
"""

from __future__ import annotations

from dataclasses import dataclass

import matplotlib.pyplot as plt
import osmnx as ox
from geopandas import GeoDataFrame
from networkx import MultiDiGraph
from tqdm import tqdm

from ..models import FontSet, PosterConfig
from ..osm import fetch_features, fetch_graph
from ..output import save_poster
from .layers import (
    apply_viewport,
    render_gradients,
    render_parks,
    render_roads,
    render_typography,
    render_water,
)
from .viewport import get_crop_limits, setup_figure


@dataclass
class MapData:
    """All fetched OSM data needed for rendering."""

    graph: MultiDiGraph
    water: GeoDataFrame | None
    parks: GeoDataFrame | None


def fetch_map_data(config: PosterConfig, compensated_dist: int) -> MapData:
    """
    Fetch all OSM data (street network, water, parks) with progress bar.

    Args:
        config: Poster configuration
        compensated_dist: Distance compensated for aspect ratio

    Returns:
        MapData with all fetched data

    Raises:
        RuntimeError: If street network data cannot be retrieved
    """
    with tqdm(
        total=3,
        desc="Fetching map data",
        unit="step",
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}",
    ) as pbar:
        # 1. Fetch Street Network
        pbar.set_description("Downloading street network")
        g = fetch_graph(config.center, compensated_dist)
        if g is None:
            raise RuntimeError("Failed to retrieve street network data.")
        pbar.update(1)

        # 2. Fetch Water Features
        pbar.set_description("Downloading water features")
        water = fetch_features(
            config.center,
            compensated_dist,
            tags={"natural": ["water", "bay", "strait"], "waterway": "riverbank"},
            name="water",
        )
        pbar.update(1)

        # 3. Fetch Parks
        pbar.set_description("Downloading parks/green spaces")
        parks = fetch_features(
            config.center,
            compensated_dist,
            tags={"leisure": "park", "landuse": "grass"},
            name="parks",
        )
        pbar.update(1)

    print("\u2713 All data retrieved successfully!")
    return MapData(graph=g, water=water, parks=parks)


def compose_poster(
    config: PosterConfig, default_fonts: FontSet | None = None
) -> str:
    """
    Orchestrate the full poster rendering pipeline.

    Args:
        config: Complete poster configuration
        default_fonts: Default FontSet (Roboto) for attribution text

    Returns:
        Path to the saved output file
    """
    print(f"\nGenerating map for {config.city}, {config.country}...")

    # Compute compensated distance for viewport crop
    compensated_dist = int(
        config.dist
        * (max(config.height, config.width) / min(config.height, config.width))
        / 4
    )

    # Fetch all map data
    map_data = fetch_map_data(config, compensated_dist)

    # Setup figure
    print("Rendering map...")
    fig, ax = setup_figure(config)

    # Project graph to metric CRS
    g_proj = ox.project_graph(map_data.graph)

    # Render layers in order
    render_water(ax, map_data.water, g_proj, config)
    render_parks(ax, map_data.parks, g_proj, config)
    render_roads(ax, g_proj, config)

    # Apply viewport crop
    crop_xlim, crop_ylim = get_crop_limits(
        g_proj, config.center, fig, compensated_dist
    )
    apply_viewport(ax, crop_xlim, crop_ylim)

    # Render overlays
    render_gradients(ax, config)
    render_typography(ax, config, default_fonts)

    # Save and cleanup
    save_poster(fig, config)
    plt.close(fig)

    return config.output_file

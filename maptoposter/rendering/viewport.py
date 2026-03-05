"""
Viewport and figure setup for poster rendering.

Handles matplotlib figure creation and geographic crop limit calculations
to maintain the poster's aspect ratio.
"""

from __future__ import annotations

import osmnx as ox
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from networkx import MultiDiGraph
from shapely.geometry import Point

from ..models import Coordinates, PosterConfig


def setup_figure(config: PosterConfig) -> tuple[Figure, Axes]:
    """
    Create matplotlib figure with correct size and background color.

    Args:
        config: Poster configuration

    Returns:
        Tuple of (Figure, Axes) ready for rendering
    """
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(
        figsize=(config.width, config.height), facecolor=config.theme.bg
    )
    ax.set_facecolor(config.theme.bg)
    ax.set_position((0.0, 0.0, 1.0, 1.0))
    return fig, ax


def get_crop_limits(
    g_proj: MultiDiGraph,
    center: Coordinates,
    fig: Figure,
    dist: float,
) -> tuple[tuple[float, float], tuple[float, float]]:
    """
    Crop inward to preserve aspect ratio while guaranteeing
    full coverage of the requested radius.

    Args:
        g_proj: Projected graph (metric CRS)
        center: Map center coordinates
        fig: Matplotlib figure (for aspect ratio)
        dist: Compensated distance in meters

    Returns:
        Tuple of ((x_min, x_max), (y_min, y_max)) crop limits
    """
    # Project center point into graph CRS
    center_pt = ox.projection.project_geometry(
        Point(center.longitude, center.latitude),
        crs="EPSG:4326",
        to_crs=g_proj.graph["crs"],
    )[0]
    center_x, center_y = center_pt.x, center_pt.y

    fig_width, fig_height = fig.get_size_inches()
    aspect = fig_width / fig_height

    # Start from the requested radius
    half_x = dist
    half_y = dist

    # Cut inward to match aspect
    if aspect > 1:  # landscape -> reduce height
        half_y = half_x / aspect
    else:  # portrait -> reduce width
        half_x = half_y * aspect

    return (
        (center_x - half_x, center_x + half_x),
        (center_y - half_y, center_y + half_y),
    )

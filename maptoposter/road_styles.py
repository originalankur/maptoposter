"""
Road styling based on OpenStreetMap highway classification.

Provides a unified single-pass computation of both edge colors and widths,
replacing the duplicate iteration in the original code.
"""

from __future__ import annotations

from dataclasses import dataclass

from networkx import MultiDiGraph

from . import constants
from .models import RoadColors

# Highway type to tier mapping (single source of truth)
HIGHWAY_TIERS: dict[str, str] = {}
for _tier, _types in {
    "motorway": ["motorway", "motorway_link"],
    "primary": ["trunk", "trunk_link", "primary", "primary_link"],
    "secondary": ["secondary", "secondary_link"],
    "tertiary": ["tertiary", "tertiary_link"],
    "residential": ["residential", "living_street", "unclassified"],
}.items():
    for _t in _types:
        HIGHWAY_TIERS[_t] = _tier

# Width by tier
TIER_WIDTHS: dict[str, float] = {
    "motorway": constants.ROAD_WIDTH_MOTORWAY,
    "primary": constants.ROAD_WIDTH_PRIMARY,
    "secondary": constants.ROAD_WIDTH_SECONDARY,
    "tertiary": constants.ROAD_WIDTH_TERTIARY,
    "residential": constants.ROAD_WIDTH_DEFAULT,
}


@dataclass
class EdgeStyles:
    """Colors and widths for every edge in the graph (parallel lists)."""

    colors: list[str]
    widths: list[float]


def classify_highway(highway_value: str | list[str]) -> str:
    """
    Normalize an OSM highway tag to a tier name.

    Args:
        highway_value: Highway tag value (string or list of strings)

    Returns:
        Tier name ('motorway', 'primary', 'secondary', 'tertiary',
        'residential', or 'default')
    """
    if isinstance(highway_value, list):
        highway_value = highway_value[0] if highway_value else "unclassified"
    return HIGHWAY_TIERS.get(highway_value, "default")


def compute_edge_styles(graph: MultiDiGraph, road_colors: RoadColors) -> EdgeStyles:
    """
    Single pass over all edges to compute both colors and widths.

    Args:
        graph: Projected street network graph
        road_colors: Color assignments from the theme

    Returns:
        EdgeStyles with parallel colors and widths lists
    """
    colors: list[str] = []
    widths: list[float] = []

    color_map = {
        "motorway": road_colors.motorway,
        "primary": road_colors.primary,
        "secondary": road_colors.secondary,
        "tertiary": road_colors.tertiary,
        "residential": road_colors.residential,
        "default": road_colors.default,
    }

    for _u, _v, data in graph.edges(data=True):
        tier = classify_highway(data.get("highway", "unclassified"))
        colors.append(color_map.get(tier, road_colors.default))
        widths.append(TIER_WIDTHS.get(tier, constants.ROAD_WIDTH_DEFAULT))

    return EdgeStyles(colors=colors, widths=widths)

"""
OpenStreetMap data fetching via OSMnx.

Handles downloading and caching of street networks and geographic features
(water, parks) from the Overpass API.
"""

from __future__ import annotations

import time
from typing import Any, cast

import osmnx as ox
from geopandas import GeoDataFrame
from networkx import MultiDiGraph

from . import constants
from .cache import CacheError, cache_get, cache_set
from .models import Coordinates


def fetch_graph(point: Coordinates, dist: int) -> MultiDiGraph | None:
    """
    Fetch street network graph from OpenStreetMap.

    Uses caching to avoid redundant downloads. Fetches all network types
    within the specified distance from the center point.

    Args:
        point: Coordinates for center point
        dist: Distance in meters from center point

    Returns:
        MultiDiGraph of street network, or None if fetch fails
    """
    lat, lon = point.latitude, point.longitude
    cache_key = f"graph_{lat}_{lon}_{dist}"
    cached = cache_get(cache_key)
    if cached is not None:
        print("\u2713 Using cached street network")
        return cast(MultiDiGraph, cached)

    try:
        g = ox.graph_from_point(
            point.as_tuple(),
            dist=dist,
            dist_type="bbox",
            network_type="all",
            truncate_by_edge=True,
        )
        time.sleep(constants.GRAPH_FETCH_DELAY)
        try:
            cache_set(cache_key, g)
        except CacheError as e:
            print(e)
        return g
    except Exception as e:
        print(f"OSMnx error while fetching graph: {e}")
        return None


def fetch_features(
    point: Coordinates, dist: int, tags: dict[str, Any], name: str
) -> GeoDataFrame | None:
    """
    Fetch geographic features (water, parks, etc.) from OpenStreetMap.

    Uses caching to avoid redundant downloads. Fetches features matching
    the specified OSM tags within distance from center point.

    Args:
        point: Coordinates for center point
        dist: Distance in meters from center point
        tags: Dictionary of OSM tags to filter features
        name: Name for this feature type (for caching and logging)

    Returns:
        GeoDataFrame of features, or None if fetch fails
    """
    lat, lon = point.latitude, point.longitude
    tag_str = "_".join(tags.keys())
    cache_key = f"{name}_{lat}_{lon}_{dist}_{tag_str}"
    cached = cache_get(cache_key)
    if cached is not None:
        print(f"\u2713 Using cached {name}")
        return cast(GeoDataFrame, cached)

    try:
        data = ox.features_from_point(point.as_tuple(), tags=tags, dist=dist)
        time.sleep(constants.FEATURE_FETCH_DELAY)
        try:
            cache_set(cache_key, data)
        except CacheError as e:
            print(e)
        return data
    except Exception as e:
        print(f"OSMnx error while fetching features: {e}")
        return None

"""
Pickle-based caching for expensive API calls (geocoding, OSM data).
"""

from __future__ import annotations

import os
import pickle
from pathlib import Path
from typing import Any

from . import constants


class CacheError(Exception):
    """Raised when a cache operation fails."""


def _cache_path(key: str, cache_dir: Path | None = None) -> str:
    """
    Generate a safe cache file path from a cache key.

    Args:
        key: Cache key identifier
        cache_dir: Override cache directory (defaults to constants.CACHE_DIR)

    Returns:
        Path to cache file with .pkl extension
    """
    cache_dir = cache_dir or constants.CACHE_DIR
    safe = key.replace(os.sep, "_")
    return os.path.join(cache_dir, f"{safe}.pkl")


def cache_get(key: str, cache_dir: Path | None = None) -> Any | None:
    """
    Retrieve a cached object by key.

    Args:
        key: Cache key identifier
        cache_dir: Override cache directory

    Returns:
        Cached object if found, None otherwise

    Raises:
        CacheError: If cache read operation fails
    """
    try:
        path = _cache_path(key, cache_dir)
        if not os.path.exists(path):
            return None
        with open(path, "rb") as f:
            return pickle.load(f)
    except Exception as e:
        raise CacheError(f"Cache read failed: {e}") from e


def cache_set(key: str, value: Any, cache_dir: Path | None = None) -> None:
    """
    Store an object in the cache.

    Args:
        key: Cache key identifier
        value: Object to cache (must be picklable)
        cache_dir: Override cache directory

    Raises:
        CacheError: If cache write operation fails
    """
    try:
        cache_dir = cache_dir or constants.CACHE_DIR
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        path = _cache_path(key, cache_dir)
        with open(path, "wb") as f:
            pickle.dump(value, f, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception as e:
        raise CacheError(f"Cache write failed: {e}") from e

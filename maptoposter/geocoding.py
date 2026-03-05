"""
Geocoding via Nominatim (geopy).

Converts city/country names to geographic coordinates with caching
and rate limiting.
"""

from __future__ import annotations

import asyncio
import time

from geopy.geocoders import Nominatim

from . import constants
from .cache import CacheError, cache_get, cache_set
from .models import Coordinates


def get_coordinates(city: str, country: str) -> Coordinates:
    """
    Fetch coordinates for a given city and country using geopy.
    Includes rate limiting to be respectful to the geocoding service.

    Args:
        city: City name
        country: Country name

    Returns:
        Coordinates dataclass with latitude and longitude

    Raises:
        ValueError: If geocoding fails or returns no result
    """
    cache_key = f"coords_{city.lower()}_{country.lower()}"
    cached = cache_get(cache_key)
    if cached:
        print(f"\u2713 Using cached coordinates for {city}, {country}")
        # Handle both old tuple format and new Coordinates format
        if isinstance(cached, tuple):
            return Coordinates(latitude=cached[0], longitude=cached[1])
        return cached

    print("Looking up coordinates...")
    geolocator = Nominatim(user_agent="city_map_poster", timeout=10)

    # Add a small delay to respect Nominatim's usage policy
    time.sleep(constants.GEOCODING_DELAY)

    try:
        location = geolocator.geocode(f"{city}, {country}")
    except Exception as e:
        raise ValueError(f"Geocoding failed for {city}, {country}: {e}") from e

    # If geocode returned a coroutine in some environments, run it to get the result.
    if asyncio.iscoroutine(location):
        try:
            location = asyncio.run(location)
        except RuntimeError as exc:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                raise RuntimeError(
                    "Geocoder returned a coroutine while an event loop is already running. "
                    "Run this script in a synchronous environment."
                ) from exc
            location = loop.run_until_complete(location)

    if location:
        addr = getattr(location, "address", None)
        if addr:
            print(f"\u2713 Found: {addr}")
        else:
            print("\u2713 Found location (address not available)")
        print(f"\u2713 Coordinates: {location.latitude}, {location.longitude}")
        coords = Coordinates(latitude=location.latitude, longitude=location.longitude)
        try:
            # Cache as tuple for backward compatibility with existing caches
            cache_set(cache_key, (location.latitude, location.longitude))
        except CacheError as e:
            print(e)
        return coords

    raise ValueError(f"Could not find coordinates for {city}, {country}")

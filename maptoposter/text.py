"""
Text processing utilities for poster typography.

Handles script detection, city name formatting, and font property creation.
"""

from __future__ import annotations

from matplotlib.font_manager import FontProperties

from . import constants
from .models import FontSet

# Mapping from FontSet attribute names to matplotlib weight strings
_WEIGHT_MAP = {
    "bold": "bold",
    "regular": "normal",
    "light": "light",
}


def is_latin_script(text: str) -> bool:
    """
    Check if text is primarily Latin script.
    Used to determine if letter-spacing should be applied to city names.

    Args:
        text: Text to analyze

    Returns:
        True if text is primarily Latin script, False otherwise
    """
    if not text:
        return True

    latin_count = 0
    total_alpha = 0

    for char in text:
        if char.isalpha():
            total_alpha += 1
            # Latin Unicode ranges: Basic Latin through Latin Extended-B (U+0000-U+024F)
            if ord(char) < constants.LATIN_UPPER_CODEPOINT:
                latin_count += 1

    # If no alphabetic characters, default to Latin (numbers, symbols, etc.)
    if total_alpha == 0:
        return True

    # Consider it Latin if >80% of alphabetic characters are Latin
    return (latin_count / total_alpha) > constants.LATIN_SCRIPT_THRESHOLD


def format_city_display(city: str) -> str:
    """
    Format city name for poster display.

    Latin scripts get uppercase with letter spacing (e.g., "P  A  R  I  S").
    Non-Latin scripts are preserved as-is.

    Args:
        city: City display name

    Returns:
        Formatted city name string
    """
    if is_latin_script(city):
        return constants.LATIN_LETTER_SPACING.join(list(city.upper()))
    return city


def compute_city_font_size(
    city: str, base_size: float, scale_factor: float
) -> float:
    """
    Dynamically adjust font size based on city name length to prevent truncation.

    Args:
        city: City display name (not the spaced version)
        base_size: Base font size at reference dimension
        scale_factor: Scale factor based on poster dimensions

    Returns:
        Adjusted font size
    """
    base_adjusted = base_size * scale_factor
    char_count = len(city)

    if char_count > constants.CITY_NAME_LENGTH_THRESHOLD:
        length_factor = constants.CITY_NAME_LENGTH_THRESHOLD / char_count
        return max(
            base_adjusted * length_factor,
            constants.CITY_NAME_MIN_SCALE_FACTOR * scale_factor,
        )
    return base_adjusted


def make_font(
    fonts: FontSet | None, weight: str, size: float
) -> FontProperties:
    """
    Create FontProperties with fallback to system monospace.

    Args:
        fonts: FontSet with paths to font files, or None for system fallback
        weight: Font weight name ('bold', 'regular', 'light')
        size: Font size in points

    Returns:
        Configured FontProperties instance
    """
    if fonts is not None:
        return FontProperties(fname=getattr(fonts, weight), size=size)
    mpl_weight = _WEIGHT_MAP.get(weight, "normal")
    return FontProperties(family="monospace", weight=mpl_weight, size=size)

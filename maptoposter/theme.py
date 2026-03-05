"""
Theme loading and management.

Themes are JSON files in the themes/ directory that define colors for
all visual elements of the poster.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from . import constants
from .models import Theme


# Embedded fallback theme used when theme file is missing
_FALLBACK_THEME_DATA: dict[str, str] = {
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


def get_available_themes(themes_dir: Path | None = None) -> list[str]:
    """
    Scan the themes directory and return a list of available theme names.

    Args:
        themes_dir: Override themes directory path

    Returns:
        Sorted list of theme names (without .json extension)
    """
    themes_dir = themes_dir or constants.THEMES_DIR
    if not os.path.exists(themes_dir):
        os.makedirs(themes_dir)
        return []

    themes = []
    for file in sorted(os.listdir(themes_dir)):
        if file.endswith(".json"):
            themes.append(file[:-5])  # Remove .json extension
    return themes


def load_theme(
    theme_name: str = "terracotta", themes_dir: Path | None = None
) -> Theme:
    """
    Load theme from JSON file in themes directory.

    Args:
        theme_name: Name of the theme (without .json extension)
        themes_dir: Override themes directory path

    Returns:
        Theme dataclass with all color values
    """
    themes_dir = themes_dir or constants.THEMES_DIR
    theme_file = os.path.join(themes_dir, f"{theme_name}.json")

    if not os.path.exists(theme_file):
        print(f"\u26a0 Theme file '{theme_file}' not found. Using default terracotta theme.")
        return Theme.from_dict(_FALLBACK_THEME_DATA)

    with open(theme_file, "r", encoding=constants.FILE_ENCODING) as f:
        data = json.load(f)
        print(f"\u2713 Loaded theme: {data.get('name', theme_name)}")
        if "description" in data:
            print(f"  {data['description']}")
        return Theme.from_dict(data)


def list_themes(themes_dir: Path | None = None) -> None:
    """
    Print all available themes with descriptions.

    Args:
        themes_dir: Override themes directory path
    """
    themes_dir = themes_dir or constants.THEMES_DIR
    available = get_available_themes(themes_dir)
    if not available:
        print("No themes found in 'themes/' directory.")
        return

    print("\nAvailable Themes:")
    print("-" * 60)
    for theme_name in available:
        theme_path = os.path.join(themes_dir, f"{theme_name}.json")
        try:
            with open(theme_path, "r", encoding=constants.FILE_ENCODING) as f:
                theme_data = json.load(f)
                display_name = theme_data.get("name", theme_name)
                description = theme_data.get("description", "")
        except (OSError, json.JSONDecodeError):
            display_name = theme_name
            description = ""
        print(f"  {theme_name}")
        print(f"    {display_name}")
        if description:
            print(f"    {description}")
        print()

"""
Font loading and Google Fonts integration.

Handles downloading fonts from Google Fonts API, local font loading,
and caching downloaded font files.
"""

from __future__ import annotations

import os
import re
from typing import Optional

import requests

from . import constants
from .models import FontSet

# Weight names mapped to numeric values
WEIGHT_NAMES = {300: "light", 400: "regular", 700: "bold"}
DEFAULT_WEIGHTS = [300, 400, 700]


def download_google_font(
    font_family: str, weights: list[int] | None = None
) -> Optional[dict[str, str]]:
    """
    Download a font family from Google Fonts and cache it locally.

    Args:
        font_family: Google Fonts family name (e.g., 'Noto Sans JP', 'Open Sans')
        weights: List of font weights to download (300=light, 400=regular, 700=bold)

    Returns:
        Dict with 'light', 'regular', 'bold' keys mapping to font file paths,
        or None if download fails
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS

    # Create fonts cache directory
    constants.FONTS_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Normalize font family name for file paths
    font_name_safe = font_family.replace(" ", "_").lower()

    font_files: dict[str, str] = {}

    try:
        # Google Fonts API endpoint - request all weights at once
        weights_str = ";".join(map(str, weights))
        api_url = "https://fonts.googleapis.com/css2"

        params = {"family": f"{font_family}:wght@{weights_str}"}
        headers = {
            "User-Agent": "Mozilla/5.0"  # Get .woff2 files (better compression)
        }

        response = requests.get(api_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        css_content = response.text

        # Parse CSS to extract weight-specific URLs
        weight_url_map: dict[int, str] = {}
        font_face_blocks = re.split(r"@font-face\s*\{", css_content)

        for block in font_face_blocks[1:]:  # Skip first empty split
            weight_match = re.search(r"font-weight:\s*(\d+)", block)
            if not weight_match:
                continue

            weight = int(weight_match.group(1))

            url_match = re.search(r"url\((https://[^)]+\.(woff2|ttf))\)", block)
            if url_match:
                weight_url_map[weight] = url_match.group(1)

        # Download each weight
        for weight in weights:
            weight_key = WEIGHT_NAMES.get(weight, "regular")

            weight_url = weight_url_map.get(weight)

            # If exact weight not found, try closest
            if not weight_url and weight_url_map:
                closest_weight = min(
                    weight_url_map.keys(), key=lambda x: abs(x - weight)
                )
                weight_url = weight_url_map[closest_weight]
                print(
                    f"  Using weight {closest_weight} for {weight_key} "
                    f"(requested {weight} not available)"
                )

            if weight_url:
                file_ext = "woff2" if weight_url.endswith(".woff2") else "ttf"
                font_filename = f"{font_name_safe}_{weight_key}.{file_ext}"
                font_path = constants.FONTS_CACHE_DIR / font_filename

                if not font_path.exists():
                    print(f"  Downloading {font_family} {weight_key} ({weight})...")
                    try:
                        font_response = requests.get(weight_url, timeout=10)
                        font_response.raise_for_status()
                        font_path.write_bytes(font_response.content)
                    except Exception as e:
                        print(f"  \u26a0 Failed to download {weight_key}: {e}")
                        continue
                else:
                    print(f"  Using cached {font_family} {weight_key}")

                font_files[weight_key] = str(font_path)

        # Ensure we have at least regular weight
        if "regular" not in font_files and font_files:
            font_files["regular"] = list(font_files.values())[0]
            print(f"  Using {list(font_files.keys())[0]} weight as regular")

        # If we don't have all three weights, duplicate available ones
        if "bold" not in font_files and "regular" in font_files:
            font_files["bold"] = font_files["regular"]
            print("  Using regular weight as bold")
        if "light" not in font_files and "regular" in font_files:
            font_files["light"] = font_files["regular"]
            print("  Using regular weight as light")

        return font_files if font_files else None

    except Exception as e:
        print(f"\u26a0 Error downloading Google Font '{font_family}': {e}")
        return None


def load_fonts(font_family: str | None = None) -> FontSet | None:
    """
    Load fonts from local directory or download from Google Fonts.

    Args:
        font_family: Google Fonts family name (e.g., 'Noto Sans JP', 'Open Sans').
                     If None, uses local Roboto fonts.

    Returns:
        FontSet with paths to font files, or None if all loading methods fail
    """
    # If custom font family specified, try to download from Google Fonts
    if font_family and font_family.lower() != "roboto":
        print(f"Loading Google Font: {font_family}")
        fonts = download_google_font(font_family)
        if fonts:
            print(f"\u2713 Font '{font_family}' loaded successfully")
            return FontSet.from_dict(fonts)
        print(f"\u26a0 Failed to load '{font_family}', falling back to local Roboto")

    # Default: Load local Roboto fonts
    fonts_dir = constants.FONTS_DIR
    font_paths = {
        "bold": os.path.join(fonts_dir, "Roboto-Bold.ttf"),
        "regular": os.path.join(fonts_dir, "Roboto-Regular.ttf"),
        "light": os.path.join(fonts_dir, "Roboto-Light.ttf"),
    }

    # Verify fonts exist
    for _weight, path in font_paths.items():
        if not os.path.exists(path):
            print(f"\u26a0 Font not found: {path}")
            return None

    return FontSet.from_dict(font_paths)

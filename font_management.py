"""
Font Management Module
Handles font loading, Google Fonts integration, and caching.
"""

import os
import re
from pathlib import Path
from typing import Optional

import requests

FONTS_DIR = "fonts"
FONTS_CACHE_DIR = Path(FONTS_DIR) / "cache"


def download_google_font(font_family: str, weights: list = None) -> Optional[dict]:
    """
    Download a font family from Google Fonts and cache it locally.
    Returns dict with font paths for different weights, or None if download fails.

    :param font_family: Google Fonts family name (e.g., 'Noto Sans JP', 'Open Sans')
    :param weights: List of font weights to download (300=light, 400=regular, 700=bold)
    :return: Dict with 'light', 'regular', 'bold' keys mapping to font file paths
    """
    if weights is None:
        weights = [300, 400, 700]

    # Create fonts cache directory
    FONTS_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Normalize font family name for file paths
    font_name_safe = font_family.replace(" ", "_").lower()

    font_files = {}

    try:
        # Google Fonts API endpoint - request all weights at once
        weights_str = ";".join(map(str, weights))
        api_url = "https://fonts.googleapis.com/css2"

        # Use requests library for cleaner HTTP handling
        params = {"family": f"{font_family}:wght@{weights_str}"}
        headers = {
            "User-Agent": "Mozilla/5.0"  # Get .woff2 files (better compression)
        }

        # Fetch CSS file
        response = requests.get(api_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        css_content = response.text

        # Parse CSS to extract weight-specific URLs
        # Google Fonts CSS has @font-face blocks with font-weight and src: url()
        weight_url_map = {}

        # Split CSS into font-face blocks
        font_face_blocks = re.split(r"@font-face\s*\{", css_content)

        for block in font_face_blocks[1:]:  # Skip first empty split
            # Extract font-weight
            weight_match = re.search(r"font-weight:\s*(\d+)", block)
            if not weight_match:
                continue

            weight = int(weight_match.group(1))

            # Extract URL (prefer woff2, fallback to ttf)
            url_match = re.search(r"url\((https://[^)]+\.(woff2|ttf))\)", block)
            if url_match:
                weight_url_map[weight] = url_match.group(1)

        # Map weights to our keys
        weight_map = {300: "light", 400: "regular", 700: "bold"}

        # Download each weight
        for weight in weights:
            weight_key = weight_map.get(weight, "regular")

            # Find URL for this weight
            weight_url = weight_url_map.get(weight)

            # If exact weight not found, try to find closest
            if not weight_url and weight_url_map:
                # Find closest weight
                closest_weight = min(
                    weight_url_map.keys(), key=lambda x: abs(x - weight)
                )
                weight_url = weight_url_map[closest_weight]
                print(
                    f"  Using weight {closest_weight} for {weight_key} (requested {weight} not available)"
                )

            if weight_url:
                # Determine file extension
                file_ext = "woff2" if weight_url.endswith(".woff2") else "ttf"

                # Download font file
                font_filename = f"{font_name_safe}_{weight_key}.{file_ext}"
                font_path = FONTS_CACHE_DIR / font_filename

                if not font_path.exists():
                    print(f"  Downloading {font_family} {weight_key} ({weight})...")
                    try:
                        font_response = requests.get(weight_url, timeout=10)
                        font_response.raise_for_status()
                        font_path.write_bytes(font_response.content)
                    except Exception as e:
                        print(f"  ⚠ Failed to download {weight_key}: {e}")
                        continue
                else:
                    print(f"  Using cached {font_family} {weight_key}")

                font_files[weight_key] = str(font_path)

        # Ensure we have at least regular weight
        if "regular" not in font_files and font_files:
            # Use first available as regular
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
        print(f"⚠ Error downloading Google Font '{font_family}': {e}")
        return None


def load_fonts(font_family: Optional[str] = None) -> Optional[dict]:
    """
    Load fonts from local directory or download from Google Fonts.
    
    Priority order:
    1. Local font files in fonts/ directory
    2. Google Fonts download
    3. Default Roboto fonts
    
    Args:
        font_family: Font family name (e.g., 'Noto Sans Arabic', 'NRT').
                    If None, uses local Roboto fonts.
                    
    Returns:
        dict: Font paths for 'bold', 'regular', 'light' weights,
              or None if all loading methods fail
    """
    # Check local fonts directory first for custom font families
    if font_family and font_family.lower() != "roboto":
        # Search for font files with various naming patterns
        local_font_patterns = [
            f"{font_family}-Reg.ttf",
            f"{font_family}-Regular.ttf",
            f"{font_family}.ttf",
            f"{font_family}-Bold.ttf",
            f"{font_family}-Bd.ttf",
            f"{font_family}-Light.ttf",
        ]
        
        local_fonts = {}
        for pattern in local_font_patterns:
            font_path = os.path.join(FONTS_DIR, pattern)
            if os.path.exists(font_path):
                # Categorize font by weight based on filename
                pattern_lower = pattern.lower()
                if "light" in pattern_lower:
                    local_fonts["light"] = font_path
                elif "bold" in pattern_lower or "-bd" in pattern_lower:
                    local_fonts["bold"] = font_path
                else:
                    local_fonts["regular"] = font_path
        
        # Use local fonts if found
        if local_fonts:
            print(f"Using local font: {font_family}")
            
            # Fill missing weights with available ones
            if "regular" in local_fonts:
                base_font = local_fonts["regular"]
                local_fonts.setdefault("bold", base_font)
                local_fonts.setdefault("light", base_font)
            elif local_fonts:
                # Use any available font as fallback for missing weights
                base_font = list(local_fonts.values())[0]
                for weight in ["regular", "bold", "light"]:
                    local_fonts.setdefault(weight, base_font)
            
            print(f"✓ Font '{font_family}' loaded successfully from local fonts")
            return local_fonts
        
        # If not found locally, try to download from Google Fonts
        print(f"Loading Google Font: {font_family}")
        fonts = download_google_font(font_family)
        if fonts:
            print(f"✓ Font '{font_family}' loaded successfully")
            return fonts

        print(f"⚠ Failed to load '{font_family}', falling back to local Roboto")

    # Default: Load local Roboto fonts
    fonts = {
        "bold": os.path.join(FONTS_DIR, "Roboto-Bold.ttf"),
        "regular": os.path.join(FONTS_DIR, "Roboto-Regular.ttf"),
        "light": os.path.join(FONTS_DIR, "Roboto-Light.ttf"),
    }

    # Verify fonts exist
    for _weight, path in fonts.items():
        if not os.path.exists(path):
            print(f"⚠ Font not found: {path}")
            return None

    return fonts

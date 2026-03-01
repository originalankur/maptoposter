"""
Font Management Module
Handles font loading, Google Fonts integration, and caching.
"""

import os
import re
from pathlib import Path
from typing import Optional, Union

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


def load_fonts_from_path(font_path: Union[str, Path]) -> Optional[dict]:
    """
    Load fonts from a local file path.
    Handles both single font files and directories with multiple font weights.

    Supports:
    - Single font file: Uses same file for all weights (bold, regular, light)
    - Directory with weight-specific files: Looks for patterns like:
      * filename-bold.ttf, filename-regular.ttf, filename-light.ttf
      * filename_bold.ttf, filename_regular.ttf, filename_light.ttf
      * bold.ttf, regular.ttf, light.ttf
      * fontname-700.ttf, fontname-400.ttf, fontname-300.ttf (numeric weights)

    Supported formats: .ttf, .otf, .woff, .woff2

    Args:
        font_path: Path to font file or directory containing fonts.
                  Can be absolute or relative path.

    Returns:
        Dict with 'bold', 'regular', 'light' keys mapping to font file paths,
        or None if path is invalid or no suitable fonts found.
    """
    # Convert to Path object for robust path handling
    font_path = Path(font_path).expanduser().resolve()

    # Check if path exists
    if not font_path.exists():
        print(f"⚠ Font path does not exist: {font_path}")
        return None

    # Supported font extensions
    SUPPORTED_EXTS = {".ttf", ".otf", ".woff", ".woff2"}

    # Single file case
    if font_path.is_file():
        if font_path.suffix.lower() not in SUPPORTED_EXTS:
            print(
                f"⚠ Unsupported font format: {font_path.suffix}. "
                f"Supported: {', '.join(SUPPORTED_EXTS)}"
            )
            return None

        # Use the same file for all weights
        font_files = {
            "bold": str(font_path),
            "regular": str(font_path),
            "light": str(font_path),
        }
        print(f"✓ Loaded font from: {font_path}")
        return font_files

    # Directory case
    if font_path.is_dir():
        font_files = {}

        # Find all font files in directory
        font_candidates = [
            f for f in font_path.iterdir()
            if f.is_file() and f.suffix.lower() in SUPPORTED_EXTS
        ]

        if not font_candidates:
            print(f"⚠ No font files found in: {font_path}")
            return None

        # Weight patterns to search for (in priority order)
        weight_patterns = {
            "bold": [
                r"bold",
                r"700",  # Numeric weight
                r"^b_",  # Prefix style
            ],
            "regular": [
                r"regular",
                r"400",  # Numeric weight
                r"normal",
                r"^r_",  # Prefix style
            ],
            "light": [
                r"light",
                r"300",  # Numeric weight
                r"thin",
                r"^l_",  # Prefix style
            ],
        }

        # Try to match fonts to weights
        for weight_name, patterns in weight_patterns.items():
            for candidate in font_candidates:
                candidate_name = candidate.stem.lower()
                if any(re.search(pattern, candidate_name) for pattern in patterns):
                    font_files[weight_name] = str(candidate)
                    break

        # Fallback: Use first available font for missing weights
        if font_candidates and font_files:
            first_font = str(font_candidates[0])
            if "regular" not in font_files:
                font_files["regular"] = first_font
            if "bold" not in font_files:
                font_files["bold"] = first_font
            if "light" not in font_files:
                font_files["light"] = first_font
        elif font_candidates and not font_files:
            # If no weight patterns matched, use available fonts
            first_font = str(font_candidates[0])
            font_files = {
                "bold": first_font,
                "regular": first_font,
                "light": first_font,
            }

        if font_files:
            print(f"✓ Loaded fonts from directory: {font_path}")
            for weight, path in font_files.items():
                print(f"  {weight}: {Path(path).name}")
            return font_files
        else:
            print(f"⚠ Could not find suitable fonts in: {font_path}")
            return None

    print(f"⚠ Invalid path (not a file or directory): {font_path}")
    return None


def load_fonts(font_family: Optional[str] = None, font_path: Optional[Union[str, Path]] = None) -> Optional[dict]:
    """
    Load fonts from local path, Google Fonts, or default local directory.
    Returns dict with font paths for different weights.

    Priority:
    1. If font_family provided, download from Google Fonts
    2. If font_path provided, load from that local path
    3. Fall back to default local Roboto fonts

    Args:
        font_family: Google Fonts family name (e.g., 'Noto Sans JP', 'Open Sans').
                    Ignored if font_path is provided.
        font_path: Path to local font file or directory containing fonts.
                  Supports absolute or relative paths.

    Returns:
        Dict with 'bold', 'regular', 'light' keys mapping to font file paths,
        or None if all loading methods fail.
    """
    # Priority 1: Download from Google Fonts if family specified
    if font_family and font_family.lower() != "roboto":
        print(f"Loading Google Font: {font_family}")
        fonts = download_google_font(font_family)
        if fonts:
            print(f"✓ Font '{font_family}' loaded successfully")
            return fonts
        print(f"⚠ Failed to load '{font_family}', trying local font path (if provided)...")

    # Priority 2: Load from local path if provided
    if font_path:
        fonts = load_fonts_from_path(font_path)
        if fonts:
            return fonts
        print("⚠ Failed to load from font path, falling back to Roboto...")

    # Priority 3: Load default local Roboto fonts
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

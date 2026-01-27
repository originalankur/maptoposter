#!/bin/bash

# This script generates variations of map posters for Bengaluru, India
# based on the options and guides described in the README.md

# Ensure we are in the project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

echo "===================================================="
echo "Generating All Variations for Bengaluru, India"
echo "===================================================="

# 1. Basic usage
echo "--- Basic usage ---"
uv run python3 create_map_poster.py -c "Bengaluru" -C "India"

# 2. Themes (from Distance Guide & Themes section)
echo "--- Theme Variations ---"
themes=(
    "gradient_roads" 
    "contrast_zones" 
    "noir" 
    "midnight_blue" 
    "blueprint" 
    "neon_cyberpunk" 
    "warm_beige" 
    "pastel_dream" 
    "japanese_ink" 
    "emerald" 
    "forest" 
    "ocean" 
    "terracotta" 
    "sunset" 
    "autumn" 
    "copper_patina" 
    "monochrome_blue"
)

for theme in "${themes[@]}"; do
    echo "Theme: $theme"
    uv run python3 create_map_poster.py -c "Bengaluru" -C "India" -t "$theme"
done

# 3. Optional Flags (from Optional Flags table)
echo "--- Optional Flags & Overrides ---"
echo "Overriding display name and country label"
uv run python3 create_map_poster.py -c "Bengaluru" -C "India" --display-city "The Garden City" --country-label "Karnataka, India"

echo "Overriding latitude and longitude (central Bengaluru)"
uv run python3 create_map_poster.py -c "Bengaluru" -C "India" -lat 12.9716 -long 77.5946

# 4. Multilingual Support (from i18n section)
echo "--- Multilingual Support (i18n) ---"
echo "Kannada (Native script)"
uv run python3 create_map_poster.py -c "Bengaluru" -C "India" -dc "ಬೆಂಗಳೂರು" -dC "ಭಾರत (India)" --font-family "Noto Sans Kannada"

echo "Hindi (Devanagari script)"
uv run python3 create_map_poster.py -c "Bengaluru" -C "India" -dc "बेंगलुरु" -dC "भारत" --font-family "Noto Sans Devanagari"

# 5. Resolution Guide Variations
echo "--- Resolution Guide Variations ---"
echo "Instagram Post (3.6x3.6)"
uv run python3 create_map_poster.py -c "Bengaluru" -C "India" -W 3.6 -H 3.6

echo "Mobile Wallpaper (3.6x6.4)"
uv run python3 create_map_poster.py -c "Bengaluru" -C "India" -W 3.6 -H 6.4

echo "HD Wallpaper (6.4x3.6)"
uv run python3 create_map_poster.py -c "Bengaluru" -C "India" -W 6.4 -H 3.6

echo "4K Wallpaper (12.8x7.2)"
uv run python3 create_map_poster.py -c "Bengaluru" -C "India" -W 12.8 -H 7.2

echo "A4 Print (8.3x11.7)"
uv run python3 create_map_poster.py -c "Bengaluru" -C "India" -W 8.3 -H 11.7

# 6. Distance Guide Variations
echo "--- Distance Guide Variations ---"
echo "Small/Dense focal (5000m)"
uv run python3 create_map_poster.py -c "Bengaluru" -C "India" -d 5000

echo "Medium/Focused downtown (10000m)"
uv run python3 create_map_poster.py -c "Bengaluru" -C "India" -d 10000

echo "Large metro view (default 18000m)"
uv run python3 create_map_poster.py -c "Bengaluru" -C "India" -d 18000

# 7. Utility flags
echo "--- Utility Flags ---"
echo "Listing themes"
uv run python3 create_map_poster.py --list-themes

echo "Generating for ALL themes at once"
# We'll use a smaller distance to make it faster for testing
uv run python3 create_map_poster.py -c "Bengaluru" -C "India" --all-themes -d 10000

echo "===================================================="
echo "Done! Posters saved to posters/ directory."
echo "===================================================="

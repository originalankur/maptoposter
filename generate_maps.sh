#!/usr/bin/env bash
set -euo pipefail

VENUES="data/venues.csv"

# Philadelphia - midnight blue
uv run python create_map_poster.py -c "Philadelphia" -C "USA" -t midnight_blue -d 12000 --venues "$VENUES"

# New York - noir (centered on midtown for full Manhattan)
uv run python create_map_poster.py -c "New York" -C "USA" -t noir -d 14000 -lat 40.75 -long -73.98 --venues "$VENUES"

# Estes Park - forest (wider radius for mountain venues)
uv run python create_map_poster.py -c "Estes Park" -C "USA" -t forest -d 15000 --venues "$VENUES"

# Newark - emerald
uv run python create_map_poster.py -c "Newark" -C "USA" -t emerald -d 10000 --venues "$VENUES"

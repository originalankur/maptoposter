# Map Orientation Rotation (`--orientation-offset`)

This document explains the changes made to support map orientation rotation relative to north.

## Summary

A new CLI option was added:

- `--orientation-offset` (short: `-O`)
- Type: `float`
- Allowed range: `-180` to `180`
- Semantics:
  - Positive values: clockwise rotation from north
  - Negative values: counterclockwise rotation from north

Example:

```bash
python create_map_poster.py -c "Paris" -C "France" -O 30
python create_map_poster.py -c "Paris" -C "France" -O -45
```

North badge behavior:

- `--show-north` enables the badge
- `--show-north true|false` sets explicit boolean value
- `--hide-north` forces it off
- Default is dynamic:
  - `false` when `--orientation-offset` is `0`
  - `true` when `--orientation-offset` is non-zero

## What Changed

### 1. New CLI argument and validation

In `create_map_poster.py`:

- Added argument parsing for `--orientation-offset` / `-O`.
- Added validation to enforce `-180 <= value <= 180`.
- Passed the value through to `create_poster(...)`.

Why:

- Keeps the feature explicit and user-controlled.
- Prevents invalid rotations from entering the rendering pipeline.

### 2. Rotation implementation in rendering pipeline

In `create_map_poster.py`:

- Added `get_projected_center(...)` to get center coordinates in projected CRS.
- Added `rotate_graph_and_features(...)` to rotate:
  - street network node coordinates (`x`, `y`)
  - edge geometries (when present)
  - polygon feature layers (water, parks)
- Applied rotation before plotting layers in `create_poster(...)`.

Why:

- Rotation must happen in a metric projected CRS (not raw lat/lon) so geometry transforms are correct.
- Rotating around the projected map center preserves the intended focus point.
- Rotating roads and polygon layers together keeps all visual layers aligned.

### 3. README updates

In `README.md`:

- Added `--orientation-offset` to the options table.
- Added a usage example showing map rotation.

Why:

- Makes the new feature discoverable and self-documenting for users.

### 4. North orientation badge

In `create_map_poster.py`:

- Added `draw_north_badge(...)` to render a compact north indicator.
- Added CLI flags:
  - `--show-north [true/false]`
  - `--hide-north`
- Added dynamic default resolution logic based on `--orientation-offset`.

Why:

- When map orientation is rotated, users need a visual reference for true north.
- The dynamic default keeps the default map clean while still helping interpretation for rotated maps.

Design details:

- Badge colors use the existing theme palette (`THEME["bg"]` and `THEME["text"]`).
- The arrow direction reflects geographic north in local map coordinates.

## Dependency Rationale

No new external package dependency was added to `requirements.txt` or `pyproject.toml`.

Only this import was added:

```python
from shapely import affinity
```

Why this was added:

- `shapely.affinity.rotate(...)` provides robust geometric rotation for lines/polygons.
- `shapely` is already part of the existing geospatial stack used by this project (via OSMnx/GeoPandas workflows), so this is an internal module usage change, not a new third-party dependency.

In short:

- New import: yes (`shapely.affinity`)
- New install-time dependency: no

## What Is CRS, and Why It Matters

CRS means **Coordinate Reference System**. It defines how coordinates map to real places on Earth.

Common examples:

- `EPSG:4326`: geographic coordinates in latitude/longitude (degrees)
- Projected CRS (used by OSMnx when projecting): planar coordinates in meters

Why CRS is important for rotation:

- Geometry transforms like rotation are most reliable in a **projected CRS** (linear units, typically meters).
- Latitude/longitude are angular units on a curved surface, so direct planar rotation there can distort distances/angles.
- In this implementation, the center point is projected to the graph CRS first, then all map layers are rotated around that projected center.

Result:

- Rotation behaves consistently and keeps roads/water/parks aligned.
- The map remains centered on the requested location after rotation.

## Behavioral Notes

- `0` means no rotation (current behavior preserved).
- Orientation offset affects map geometry orientation, not poster aspect orientation (`--width`/`--height` still control portrait vs landscape).
- Crop logic and text layout remain unchanged.

---
name: repo-architecture
description: "How repo is organized and where a change belongs: modules, entry points, data flow, and common task recipes. Modules: poster-generation-core (create_map_poster.py); font-management (font_management.py); theme-library (themes); test-harness (test/all_variations.sh); ci-config (.github/workflows)."
---

<!-- generated-by: skillgen v0.0.0-dev | repo: repo | commit: 6d03069f34558494ccc7fc2a7de87df7a7543fd5 | date: 2026-08-06T07:56:23Z -->
# Architecture

## Overview
Single-script application that generates high-resolution, themed city map posters from OpenStreetMap data. It fetches and caches geospatial data, applies JSON-defined color themes and custom fonts, and renders poster-ready images via Matplotlib.

**Architecture style:** layered monolith (single main script plus small utility module and data assets)

## Directory map
| Path | Purpose |
|---|---|
| `create_map_poster.py` | Main application script and CLI. Handles argument parsing, theme loading, font usage, OSM/Geo data fetching and caching, layout computation, and Matplotlib rendering for posters. |
| `font_management.py` | Font management utilities. Downloads and caches Google Fonts, or loads local Roboto fonts, returning paths used by the main script when configuring Matplotlib text rendering. |
| `themes` | Collection of JSON theme definitions (colors, background, road styles, water/parks) used to style map posters. Each file is a named theme selectable via CLI. |
| `test` | Integration-style test harness. Contains shell script all_variations.sh that exercises create_map_poster.py over many parameter combinations to validate themes and layouts. |
| `.github` | GitHub-specific automation. workflows/ contains CI configuration (e.g., PR checks, conflict detection) for linting and basic validation. |
| `.flake8` | Flake8 configuration for linting style and basic static checks. |
| `.gitignore` | Git ignore rules for cache, build artifacts, virtual environments, IDE and OS files. |
| `CHANGELOG.md` | Human-maintained change log describing feature additions and fixes between versions. |
| `LICENSE` | Project license file governing usage and distribution. |
| `README.md` | User-facing documentation. Explains installation, usage examples, CLI options, and showcases example posters. |
| `pyproject.toml` | Project metadata and build configuration (PEP 621). Declares package info and dependencies. |
| `requirements.txt` | Pinned Python dependency versions for reproducible environments (GeoPandas, OSMnx, Matplotlib, etc.). |

## Entry points
- `create_map_poster.py` — Primary CLI entry point. Parses command-line arguments (city/location, size, theme, fonts, output options), orchestrates data fetching, theme application, and poster rendering.
- `test/all_variations.sh` — Shell script entry point for an integration test/job that runs create_map_poster.py with many theme/layout combinations to generate sample posters and validate output.

## Data & control flow
The main control flow starts in create_map_poster.py's CLI block, which uses argparse to collect user parameters such as location (city name or coordinates), map style, theme, poster dimensions, orientation, and font options.

1. **Initialization & configuration**: The script sets up global paths (CACHE_DIR, THEMES_DIR, FONTS_DIR, POSTERS_DIR), ensures cache directories exist, and eagerly loads fonts via FONTS = load_fonts() from font_management.

2. **Input normalization**: Helper functions like is_latin_script, generate_output_filename, get_available_themes, and load_theme normalize location names, decide filenames, and load the selected theme JSON into a Python dict with color settings.

3. **Data acquisition & caching**: get_coordinates uses geopy's Nominatim and/or lat_lon_parser to resolve a city string or explicit lat/lon into a Point. fetch_graph and fetch_features then use OSMnx and GeoPandas to download road networks and geographic layers (water, parks, etc.) for a bounding box around the coordinates. These functions wrap cache_get and cache_set to store serialized results under cache/, avoiding repeated OSM calls.

4. **Spatial processing**: get_crop_limits computes appropriate crop extents given poster aspect ratio and desired coverage, and the fetched graph/features data is filtered to those bounds. Edges are categorized by road type, and helpers like get_edge_colors_by_type and get_edge_widths_by_type map them to theme-specific colors and stroke widths.

5. **Rendering**: create_poster orchestrates Matplotlib figure creation, including gradient background (via create_gradient_fade), plotting of roads, water, and parks with theme styling, and placement of titles/subtitles using FontProperties derived from the loaded fonts. It configures DPI, figure size, and margins suitable for print-quality posters.

6. **Output generation**: The final plot is saved to the posters/ directory (or a user-specified path) using a consistent naming pattern that encodes city, theme, and timestamp. The function returns or logs the output path.

7. **Utility commands**: Additional CLI flows use print_examples to output example calls and list_themes to list available JSON themes, supporting discovery and quick testing.

Throughout, the CLI can be exercised either manually or via test/all_variations.sh, which loops over many theme and parameter combinations to stress-test rendering.

## Cross-cutting concerns
Configuration is primarily driven by environment variables and constants defined in create_map_poster.py: CACHE_DIR_PATH (from CACHE_DIR env var or 'cache'), THEMES_DIR, FONTS_DIR, and POSTERS_DIR. FILE_ENCODING is set to 'utf-8' for theme and text handling.

Logging and error handling are lightweight and mostly inline: Cache operations wrap IO in cache_get/cache_set with a custom CacheError for failure cases; font_management logs download issues and falls back to local fonts when needed. Most errors from external services (e.g., Nominatim, OSMnx, HTTP requests for fonts) are caught or allowed to bubble up with informative messages.

Fonts are a cross-cutting concern managed centrally in font_management. load_fonts controls whether custom Google Fonts or bundled Roboto fonts are used and returns a dict of paths keyed by weight ('light', 'regular', 'bold'); the main script translates these into Matplotlib FontProperties applied wherever text is rendered.

Caching is another cross-cutting concern: cache_get and cache_set provide a consistent interface for all cached artifacts (typically pickled OSMnx graphs and GeoDataFrames), ensuring that repeated runs with the same inputs are faster and reduce load on external APIs.

The project enforces basic code quality via Flake8 (configured in .flake8) and CI workflows under .github/workflows, which run linting and conflict checks on pull requests. There is no global configuration object; instead, most defaults are module-level constants, making it important for an AI agent to respect and modify them carefully when extending behavior.

## External integrations
- OpenStreetMap via OSMnx (road network and geospatial feature retrieval).
- GeoPandas and Shapely for geospatial data structures and geometry operations.
- Matplotlib (including colormaps and font management) for rendering and saving poster images.
- Geopy Nominatim geocoding service for converting city names into coordinates.
- lat_lon_parser library for parsing coordinate strings into numeric lat/lon.
- NetworkX MultiDiGraph structures for representing and manipulating the street graph.
- Google Fonts (via fonts.googleapis.com) for downloading and caching web fonts in font_management.
- Requests library for HTTP interactions with Google Fonts.
- tqdm for progress bar visualization during longer operations.

## Module inventory
| Module | Paths | Responsibility | Key dependencies |
|---|---|---|---|
| poster-generation-core | `create_map_poster.py` | End-to-end orchestration of map poster creation: CLI, caching, geocoding, data fetching, theme application, layout, and rendering. | font-management, themes, cache subsystem (cache_get/cache_set), argparse, asyncio, osmnx, geopandas, geopy, lat_lon_parser, matplotlib, networkx, shapely, numpy, tqdm |
| font-management | `font_management.py` | Abstract font loading and caching. Provides Google Fonts download support and local Roboto fallback, returning font file paths organized by weight. | requests, os, re, pathlib.Path |
| theme-library | `themes` | Curated set of JSON theme presets defining colors and styles for roads, water, parks, and backgrounds used by the poster generator. | poster-generation-core (load_theme and get_edge_colors_by_type use these JSON files), json module for parsing |
| test-harness | `test/all_variations.sh` | Shell-based integration test harness that calls the CLI with different themes and options to generate many poster examples and surface regressions. | poster-generation-core, shell environment (bash) |
| ci-config | `.github/workflows` | Continuous integration workflows for PR checks, including linting (flake8) and conflict detection. | flake8, GitHub Actions environment |

## Module dependency notes
The dependency structure is simple and largely linear:

- **poster-generation-core (create_map_poster.py)** sits at the top and depends on font-management for font loading and on the theme-library for visual styling. It also integrates with all external libraries (OSMnx, GeoPandas, Matplotlib, Geopy, etc.) and consumes configuration from constants and environment variables.

- **font-management (font_management.py)** is a leaf utility module. It does not import from create_map_poster.py or other local modules; instead it relies only on the standard library and requests. This makes it safe to reuse and extend independently. create_map_poster.py imports load_fonts from it and treats fonts as an injected resource.

- **theme-library (themes/*.json)** is a data-only module consumed by poster-generation-core via functions like get_available_themes and load_theme. No Python code depends on themes in reverse.

- **test-harness (test/all_variations.sh)** and **ci-config (.github/workflows)** both sit on the outside, invoking the main CLI or tooling but not imported by Python modules.

Layering rules to respect:
1. Keep font-management free of imports from create_map_poster.py or other application-specific modules; it should remain a generic utility.
2. Treat themes as configuration data only; new behavior should go into create_map_poster.py or a new module, not embedded in theme JSON.
3. Any new modules that orchestrate poster creation should depend on poster-generation-core rather than duplicating its logic; if they need lower-level primitives, factor those out from create_map_poster.py into reusable helpers.
4. Ensure that caching concerns remain encapsulated in cache_get/cache_set; other code should not manipulate cache files directly.
5. For AI coding agents, when adding imports or new modules, preserve the current direction of dependencies (utility modules not depending on the main script) to avoid circular imports.

## Common tasks

### Add support for exporting posters in vector formats (PDF/SVG) in addition to PNG.

1. Update CLI argument parsing in create_map_poster.py to add an '--output-format' option with choices like 'png', 'pdf', 'svg', defaulting to current behavior. Follow the pattern used for existing options (e.g., '--theme', '--size') in the argparse setup near the bottom. — `create_map_poster.py`
2. Thread the chosen output format through the call chain: extend the main() or CLI handler to pass 'output_format' into create_poster(), updating its signature and call sites accordingly. — `create_map_poster.py`
3. Inside create_poster(), adjust the Matplotlib save logic (currently using plt.savefig or fig.savefig) to select backend/parameters based on 'output_format'. Use Matplotlib's ability to save as PDF/SVG by just changing the file extension, mirroring how generate_output_filename() currently builds PNG filenames. — `create_map_poster.py`
4. Ensure generate_output_filename() includes or honors the format extension, possibly by adding an optional 'ext' parameter with default 'png', and keeping backwards compatibility with callers that don't pass it (as seen in existing calls near the CLI block). — `create_map_poster.py`
5. Update README.md 'Usage' section to document the new '--output-format' option with examples, following the style of existing CLI option documentation. — `README.md`
6. Add or extend a test in test/test_create_map_poster.py (or create it if missing) that invokes the script via subprocess or calls create_poster() directly with 'pdf' and 'svg', asserting the expected files are created in POSTERS_DIR. — `create_map_poster.py`

Verify: Run `pytest` and then an end-to-end call like `python create_map_poster.py --location "Paris" --output-format pdf` and confirm a PDF file is generated in the posters/ directory.

### Add support for user-provided custom theme JSON files via a '--theme-file' option.

1. Extend the argparse configuration in create_map_poster.py to add a mutually exclusive '--theme-file' option alongside the existing '--theme' option, using argparse's mutually_exclusive_group to avoid conflicts, reusing patterns from existing theme-related arguments. — `create_map_poster.py`
2. Update load_theme() in create_map_poster.py to accept either a theme name (current behavior) or a full file path; when '--theme-file' is provided, bypass get_available_themes() and open the JSON path directly, still using FILE_ENCODING and json.load as in the existing implementation. — `create_map_poster.py`
3. Ensure THEMES_DIR and validation logic in get_available_themes() remain unchanged for built-in themes, but document in docstrings/comments how external theme files are resolved to avoid confusion. — `create_map_poster.py`
4. Update README.md to describe how to create a custom theme JSON (using keys found in existing themes/*.json files) and how to pass it via '--theme-file'. Include a small example snippet. — `README.md`, `themes`
5. Add or update tests in test/test_themes.py (or create it) to: (1) confirm that built-in themes still load via 'load_theme("warm_beige")', and (2) create a temporary custom JSON file and verify that '--theme-file' loads it and passes colors to create_poster(). — `create_map_poster.py`

Verify: Run `pytest` and then a manual CLI run: `python create_map_poster.py --location "Berlin" --theme-file path/to/custom_theme.json` and confirm the colors match the custom theme.

### Introduce CLI flags to toggle individual layers (e.g., hide parks, show only water and roads).

1. In create_map_poster.py's argparse setup, add boolean flags like '--no-parks', '--no-water', and '--roads-only', following the dest/action style used for other boolean flags (if any) or using 'action="store_true"' as seen in other options. — `create_map_poster.py`
2. Update the data-fetching functions fetch_features() and fetch_graph() to accept a configuration object or separate parameters that indicate which layers should be fetched/drawn, threading the CLI arguments down into these functions. — `create_map_poster.py`
3. Within create_poster(), gate the plotting of parks, water, and roads based on the new flags. Use the existing plotting sections as precedents (look for where GeoDataFrames for water/parks are plotted) and wrap them in if-conditions tied to the new parameters. — `create_map_poster.py`
4. Ensure that default behavior remains identical (all layers on) when no new flags are passed, by setting default values appropriately in argparse and function signatures. — `create_map_poster.py`
5. Document the new flags in README.md under the 'Options' or 'Examples' section, showing how to generate a roads-only poster. — `README.md`
6. Add tests that call create_poster() with combinations of layer flags, verifying via Matplotlib mocking or by inspecting the number of plotted artists that parks/water layers are omitted when disabled. Use test/test_layers.py (new) or extend an existing test module. — `create_map_poster.py`

Verify: Run `pytest` and manually run `python create_map_poster.py --location "Tokyo" --roads-only` to visually confirm that only roads are rendered.

### Add a CLI option to specify a custom bounding-box size (in km or degrees) independent of poster aspect ratio.

1. Modify the CLI in create_map_poster.py to introduce a '--bbox-size' argument (e.g., in kilometers) that is optional and documented; follow the numeric option parsing pattern used for zoom/size options. — `create_map_poster.py`
2. Update get_crop_limits() to accept an explicit bbox size parameter, using it instead of or in addition to any existing size/zoom logic. Preserve current behavior when '--bbox-size' is not set. — `create_map_poster.py`
3. Ensure get_coordinates() and fetch_graph() (which depend on bounding box extents) are updated to use the new crop_limits shape, and that aspect ratio handling remains consistent with poster dimensions. — `create_map_poster.py`
4. Add comments/docstrings in get_crop_limits() clarifying how the bbox size interacts with poster size, using examples derived from existing coordinate handling code. — `create_map_poster.py`
5. Extend tests (e.g., test/test_crop_limits.py) to cover cases with and without '--bbox-size', asserting that the computed bounds change appropriately while still producing valid geometries. — `create_map_poster.py`

Verify: Run `pytest` and a manual CLI run such as `python create_map_poster.py --location "Rome" --bbox-size 10` and confirm that the spatial extent differs from the default while the poster renders.

### Add a new caching policy option to set maximum cache age and auto-prune stale OSM data.

1. Introduce a '--cache-max-age' CLI argument (e.g., in days) in create_map_poster.py, near existing cache-related configuration (CACHE_DIR, cache_get/cache_set usage). Default to current behavior when unset (no pruning). — `create_map_poster.py`
2. Extend cache_get() in create_map_poster.py to accept an optional 'max_age_seconds' argument. When set, check the cache file's modification time (via Path.stat()) and raise CacheError or return None if the entry is older than the allowed age. — `create_map_poster.py`
3. Implement a helper function (e.g., prune_cache()) in create_map_poster.py that iterates over files in CACHE_DIR and deletes those older than the max age, using the same logic as in cache_get(). Call this helper from the main CLI flow when '--cache-max-age' is provided. — `create_map_poster.py`
4. Ensure fetch_graph() and fetch_features() continue to rely on cache_get()/cache_set() without needing to know about pruning details, keeping caching concerns encapsulated as in the existing design. — `create_map_poster.py`
5. Document the new cache behavior in README.md, including how to configure '--cache-max-age' and what effect it has on runtime and data freshness. — `README.md`
6. Add tests in test/test_cache.py that create temporary cache files with spoofed modification times to verify that cache_get() respects 'max_age_seconds' and that prune_cache() removes stale entries. — `create_map_poster.py`

Verify: Run `pytest -k cache` and inspect the cache directory after running `python create_map_poster.py --location "Oslo" --cache-max-age 1` to ensure old entries are pruned.

### Introduce a batch mode CLI that reads a JSON/YAML manifest of poster specs and generates them in one run.

1. Add a '--batch-file' CLI argument in create_map_poster.py that takes a path to a manifest describing multiple posters (location, theme, size, etc.). Use argparse's mutually exclusive groups to prevent mixing single-run options and batch mode where appropriate. — `create_map_poster.py`
2. Implement a new helper function (e.g., run_batch_from_manifest(manifest_path: str)) in create_map_poster.py that reads the file (using json.load by default) and iterates over a list of job specs, invoking the same core create_poster() logic used by the standard CLI. — `create_map_poster.py`
3. Refactor the existing CLI main block to factor out a reusable 'run_single_job(args)' function so that batch mode can call into it rather than duplicating logic, following the pattern used for print_examples() or list_themes(). — `create_map_poster.py`
4. Optionally add basic YAML support by conditionally importing pyyaml if present, or by documenting that batch manifests are JSON-only unless additional dependencies are installed. Keep this logic minimal to avoid complicating requirements.txt. — `create_map_poster.py`, `requirements.txt`
5. Document the batch mode in README.md with a small example manifest file and a sample invocation of `python create_map_poster.py --batch-file posters.json`. — `README.md`
6. Create tests in test/test_batch_mode.py that write a temporary manifest with 2–3 jobs, run the batch handler, and assert that expected output files are created under POSTERS_DIR. — `create_map_poster.py`

Verify: Run `pytest -k batch` and then a manual run with a small manifest file to confirm multiple posters are generated in a single invocation.

### Add a CLI option to control road simplification/detail level for faster rendering vs high detail.

1. Add a '--road-detail' CLI option in create_map_poster.py with choices like 'low', 'medium', 'high', defaulting to current behavior (e.g., 'high'). Follow the pattern used for other choice-based options. — `create_map_poster.py`
2. Update fetch_graph() to accept a 'detail_level' parameter and adjust the OSMnx call parameters (such as 'simplify' or network filters) based on the chosen level, using existing osmnx usage as a guide for how to tune requests. — `create_map_poster.py`
3. Adjust get_edge_widths_by_type() and get_edge_colors_by_type() so they can apply different styling or filtering depending on the detail level (e.g., omit minor residential roads when 'low' is selected). Use existing road-type mapping logic as a precedent. — `create_map_poster.py`
4. Ensure that integration between detail level and caching is consistent: include detail level in cache keys (via _cache_path() or key construction) so different detail settings don't share the same cached graph, following the pattern currently used for differentiating cache entries. — `create_map_poster.py`
5. Document the new '--road-detail' option in README.md with performance vs quality trade-offs. — `README.md`
6. Add tests in test/test_road_detail.py that call fetch_graph() with different detail levels and ensure the resulting graph size (e.g., number of edges) varies as expected. — `create_map_poster.py`

Verify: Run `pytest -k road_detail` and manually generate posters with `--road-detail low` and `--road-detail high`, comparing render time and visual density.

### Implement a CLI option to choose between multiple labeling styles (minimal, standard, detailed text).

1. Add a '--label-style' CLI argument in create_map_poster.py with choices ('minimal', 'standard', 'detailed'), defaulting to the current labeling behavior (likely 'standard'). Use argparse's 'choices' parameter as with other options. — `create_map_poster.py`
2. Identify the section in create_poster() responsible for adding textual labels (city name, coordinates, subtitle). Refactor this into a helper function (e.g., draw_labels(ax, style, theme, fonts, ...)) so different styles can be implemented cleanly. — `create_map_poster.py`
3. Implement branching inside the new labeling helper to control which labels are drawn and how (font size, position, inclusion of coordinates) based on 'label_style', using existing font management via FONTS and FontProperties as a guide. — `create_map_poster.py`, `font_management.py`
4. Update print_examples() and README.md examples to mention or showcase the different labeling styles. — `create_map_poster.py`, `README.md`
5. Add tests in test/test_labels.py that call the labeling helper with each style and inspect the Matplotlib axes to ensure the correct number/type of text artists are present. — `create_map_poster.py`

Verify: Run `pytest -k labels` and manually generate posters with different `--label-style` values to visually confirm the label changes.

### Support multiple language/locale preferences for geocoding and map labels (e.g., English vs local script).

1. Extend the CLI in create_map_poster.py with a '--language' or '--locale' argument. Default to current behavior (likely system or Nominatim default). Use a string option with examples like 'en', 'de', 'ja'. — `create_map_poster.py`
2. Update get_coordinates() and the Nominatim geocoder initialization to pass the 'language' parameter, leveraging Geopy's support for localized responses (e.g., Nominatim(user_agent=..., language=lang)). — `create_map_poster.py`
3. Modify is_latin_script() or add a related helper to decide which font from FONTS to use based on the script of the label text, ensuring that non-Latin scripts select appropriate font families, reusing patterns in font_management.load_fonts(). — `create_map_poster.py`, `font_management.py`
4. Adjust create_poster()'s label drawing to use the requested language both for geocoded place names and for any static text, ensuring that encoding (FILE_ENCODING) and Matplotlib font handling are respected. — `create_map_poster.py`
5. Document language support in README.md, including any limitations (e.g., dependence on installed fonts and Nominatim's coverage). — `README.md`
6. Add tests in test/test_locale.py that mock Nominatim responses for different languages and ensure the correct strings and fonts are used when rendering labels. — `create_map_poster.py`

Verify: Run `pytest -k locale` and manually generate posters with `--language en` and `--language de` to confirm geocoded names and labels switch languages appropriately.

*See also: `repo-tech-stack` for commands/conventions, `repo-modules` for per-module guides.*

*Verified claims: 19/19.*

---
*Generated by skillgen. Regenerate with `skillgen scan <repo>`.*

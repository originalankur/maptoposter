**Fork from [originalankur/maptoposter](https://github.com/originalankur/maptoposter)**

I encountered frequent timeouts when using the original project due to unstable network access to the Nominatim service in China. 
To solve this problem, I modified the core logic to support direct latitude/longitude input, making the tool usable globally without relying on external geocoding services.

```bush
python create_map_poster.py --city "Chengdu" --country "China"
```
<img width="500"  alt="image" src="https://github.com/user-attachments/assets/bfd1dffc-2f42-426d-a72b-e956c66b7232" />


**Key Modifications:**
- **Network Adaptation**: Directly uses latitude/longitude coordinates to bypass the Nominatim geocoding service (often unreachable in China), ensuring reliable map generation.
- **CJK Localization**: Pre-configured examples for Chengdu (Chinese) and Seoul (Korean), with built-in support for Noto Sans SC and Noto Sans KR fonts.
- **Any Location Support**: No need to provide city/country names – just input coordinates, even for villages without names.


```bush
# 成都
python create_map_poster.py --city "Chengdu" --country "China" --lat 30.6598 --long 104.0633 -dc "成都" -dC "中国" --font-family "Noto Sans SC" -t warm_beige -d 12000
```
| Parameter | Description |
|:----------|:------------|
| `--lat 30.6598 --long 104.0633` | Coordinates of central Chengdu, directly bypassing external network requests. |
| `-dc "成都" -dC "中国"` | Displays Chinese names "Chengdu" and "China" on the poster. |
| `--font-family "Noto Sans SC"` | Uses a Chinese-compatible font to prevent garbled text. |
| `-t warm_beige` | Warm beige retro theme with a gentle and cozy vibe. |
| `-d 12000` | Covers a radius of 12 km, covering the main urban road network of Chengdu. |y
<img height="483" alt="chengdu_warm_beige_20260517_192142" src="https://github.com/user-attachments/assets/0989a977-7d9c-4173-a17d-b43336a13298" />

```bush
#서울
python create_map_poster.py --city "Seoul" --country "South Korea" --lat 37.5665 --long 126.9780 -dc "서울" -dC "대한민국" --font-family "Noto Sans KR" -t noir -d 15000
```

| Parameter | Description |
|:----------|:------------|
| `--lat 37.5665 --long 126.9780` | Coordinates of central Seoul (near Gyeongbokgung Palace), bypassing external network requests directly. |
| `-dc "서울" -dC "대한민국"` | Displays Korean names "Seoul" and "South Korea" on the poster. |
| `--font-family "Noto Sans KR"` | Applies Korean-supported font to avoid garbled characters. |
| `-t noir` | Pure black minimalist theme, matching the urban style of Seoul. |
| `-d 15000` | Covers a radius of 15 km, including major road networks and the Han River. |

<img width="483" alt="seoul_noir_20260517_192428" src="https://github.com/user-attachments/assets/c6de598a-c676-43f5-bab1-4408bd4a5d52" />


**1. We can add a judgment near the get_coordinates() function to completely resolve network issues.
As long as latitude and longitude are provided, the program will never access Nominatim, and there is no need to force a city name to be supplied.**

```bush
if args.latitude and args.longitude:
    coords = (args.latitude, args.longitude)
    # Use coordinates as fallback if no city name is provided
    if not args.city:
        args.city = f"{args.latitude}_{args.longitude}"
    if not args.country:
        args.country = "Unknown"
else:
    # Original Nominatim geocoding logic
    coords = get_coordinates_from_nominatim(args.city, args.country)
```


**2**
 Original Code:

```bush
if args.latitude and args.longitude:
    lat = parse(args.latitude)
    lon = parse(args.longitude)
    coords = [lat, lon]
    print(f"✓ Coordinates: {', '.join([str(i) for i in coords])}")
else:
    coords = get_coordinates(args.city, args.country, args.latitude, args.longitude)
```
Change it to:
```bush
 if args.latitude and args.longitude:
    lat = parse(args.latitude)
    lon = parse(args.longitude)
    coords = (lat, lon)  # ←change to tuple
    print(f"✓ Coordinates: {lat}, {lon}")
else:
    coords = get_coordinates(args.city, args.country, args.latitude, args.longitude)
```

**3. besides I delete the required validity and change it to intelligent judgment**

Original code:
```bush
# Validate required arguments
if not args.city or not args.country:
    print("Error: --city and --country are required.\n")
    print_examples()
    sys.exit(1)
```
Change it to:

```bush
# Validate required arguments - Only longitude and latitude are allowed to be transmitted.
if not args.city and not (args.latitude and args.longitude):
    print("Error: Either --city/--country or --lat/--long are required.\n")
    print_examples()
    sys.exit(1)

# If only coordinates are given without a city name,use latitude and longitude as the default value
if not args.city and args.latitude and args.longitude:
    args.city = f"{args.latitude}_{args.longitude}"
if not args.country and args.latitude and args.longitude:
    args.country = "Unknown"
```

**In this way, we can draw anywhere at will without city/country** 

```bush
python create_map_poster.py --lat 27.8940 --long 102.2640 -t warm_beige -d 15000 --display-city "凉山区域" --display-country "中国" --font-family "Noto Sans SC"
```
<img width="500" alt="image" src="https://github.com/user-attachments/assets/608a62f2-9947-4fbb-9c24-7d4608e0210c" />

(the picture shows the mountainous areas in western China)

<img width="250" alt="27 8940_102 2640_warm_beige_20260517_212519" src="https://github.com/user-attachments/assets/ec654fb6-521c-4bad-bec6-63528648d6c1" />

Take my hometown as an example. There are fewer roads in rural areas, so the generated images may not look very beautiful. For this reason, we can expand the scope. Maps can still be generated even without specifying cities or countries, using only latitude and longitude coordinates.

<img width="500" alt="image" src="https://github.com/user-attachments/assets/67377767-4d36-4214-97d1-58134e41d4a9" />

It can run with only latitude and longitude entered.

```bush
python create_map_poster.py --lat 28.983234 --long 105.092062 -t midnight_blue -d 30000 --display-city "MY HOMETWON" --display-country "China"
```

<img width="250" alt="28 983234_105 092062_midnight_blue_20260518_092354" src="https://github.com/user-attachments/assets/150fda5f-5542-4546-b50b-28616b6a2bc1" />

In addition, map generation is still supported by only providing the city and country names, so relevant demonstrations will be omitted for brevity.

---
**Acknowledgments**: Thanks to [originalankur](https://github.com/originalankur) for the base project, and to OpenStreetMap contributors for map data. MIT License.

________________________________________________________________________________________
> The following is the original README content, with some example images removed for brevity.

# City Map Poster Generator

Generate beautiful, minimalist map posters for any city in the world.

<img src="posters/singapore_neon_cyberpunk_20260118_153328.png" width="250">
<img src="posters/dubai_midnight_blue_20260118_140807.png" width="250">

## Installation

### With uv (Recommended)

Make sure [uv](https://docs.astral.sh/uv/) is installed. Running the script by prepending `uv run` automatically creates and manages a virtual environment.

```bash
# First run will automatically install dependencies
uv run ./create_map_poster.py --city "Paris" --country "France"

# Or sync dependencies explicitly first (using locked versions)
uv sync --locked
uv run ./create_map_poster.py --city "Paris" --country "France"
```

### With pip + venv

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

### Generate Poster

If you're using `uv`:

```bash
uv run ./create_map_poster.py --city <city> --country <country> [options]
```

Otherwise (pip + venv):

```bash
python create_map_poster.py --city <city> --country <country> [options]
```

### Required Options

| Option | Short | Description |
|--------|-------|-------------|
| `--city` | `-c` | City name (used for geocoding) |
| `--country` | `-C` | Country name (used for geocoding) |

### Optional Flags

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| **OPTIONAL:** `--latitude` | `-lat` | Override latitude center point (use with --longitude) | |
| **OPTIONAL:** `--longitude` | `-long` | Override longitude center point (use with --latitude) | |
| **OPTIONAL:** `--country-label` | | Override country text displayed on poster | |
| **OPTIONAL:** `--theme` | `-t` | Theme name | terracotta |
| **OPTIONAL:** `--distance` | `-d` | Map radius in meters | 18000 |
| **OPTIONAL:** `--list-themes` | | List all available themes | |
| **OPTIONAL:** `--all-themes` | | Generate posters for all available themes | |
| **OPTIONAL:** `--width` | `-W` | Image width in inches | 12 (max: 20) |
| **OPTIONAL:** `--height` | `-H` | Image height in inches | 16 (max: 20) |

### Multilingual Support - i18n

Display city and country names in your language with custom fonts from google fonts:

| Option | Short | Description |
|--------|-------|-------------|
| `--display-city` | `-dc` | Custom display name for city (e.g., "東京") |
| `--display-country` | `-dC` | Custom display name for country (e.g., "日本") |
| `--font-family` | | Google Fonts family name (e.g., "Noto Sans JP") |

**Examples:**

```bash
# Japanese
python create_map_poster.py -c "Tokyo" -C "Japan" -dc "東京" -dC "日本" --font-family "Noto Sans JP"

# Korean
python create_map_poster.py -c "Seoul" -C "South Korea" -dc "서울" -dC "대한민국" --font-family "Noto Sans KR"

# Arabic
python create_map_poster.py -c "Dubai" -C "UAE" -dc "دبي" -dC "الإمارات" --font-family "Cairo"
```

**Note**: Fonts are automatically downloaded from Google Fonts and cached locally in `fonts/cache/`.

### Resolution Guide (300 DPI)

Use these values for `-W` and `-H` to target specific resolutions:

| Target | Resolution (px) | Inches (-W / -H) |
|--------|-----------------|------------------|
| **Instagram Post** | 1080 x 1080 | 3.6 x 3.6 |
| **Mobile Wallpaper** | 1080 x 1920 | 3.6 x 6.4 |
| **HD Wallpaper** | 1920 x 1080 | 6.4 x 3.6 |
| **4K Wallpaper** | 3840 x 2160 | 12.8 x 7.2 |
| **A4 Print** | 2480 x 3508 | 8.3 x 11.7 |

### Usage Examples

#### Basic Examples

```bash
# Simple usage with default theme
python create_map_poster.py -c "Paris" -C "France"

# With custom theme and distance
python create_map_poster.py -c "New York" -C "USA" -t noir -d 12000
```

#### Multilingual Examples (Non-Latin Scripts)

Display city names in their native scripts:

```bash
# Japanese
python create_map_poster.py -c "Tokyo" -C "Japan" -dc "東京" -dC "日本" --font-family "Noto Sans JP" -t japanese_ink

# Korean
python create_map_poster.py -c "Seoul" -C "South Korea" -dc "서울" -dC "대한민국" --font-family "Noto Sans KR" -t midnight_blue

# Thai
python create_map_poster.py -c "Bangkok" -C "Thailand" -dc "กรุงเทพมหานคร" -dC "ประเทศไทย" --font-family "Noto Sans Thai" -t sunset

# Arabic
python create_map_poster.py -c "Dubai" -C "UAE" -dc "دبي" -dC "الإمارات" --font-family "Cairo" -t terracotta

# Chinese (Simplified)
python create_map_poster.py -c "Beijing" -C "China" -dc "北京" -dC "中国" --font-family "Noto Sans SC"

# Khmer
python create_map_poster.py -c "Phnom Penh" -C "Cambodia" -dc "ភ្នំពេញ" -dC "កម្ពុជា" --font-family "Noto Sans Khmer"
```

#### Advanced Examples

```bash
# Iconic grid patterns
python create_map_poster.py -c "New York" -C "USA" -t noir -d 12000           # Manhattan grid
python create_map_poster.py -c "Barcelona" -C "Spain" -t warm_beige -d 8000   # Eixample district

# Waterfront & canals
python create_map_poster.py -c "Venice" -C "Italy" -t blueprint -d 4000       # Canal network
python create_map_poster.py -c "Amsterdam" -C "Netherlands" -t ocean -d 6000  # Concentric canals
python create_map_poster.py -c "Dubai" -C "UAE" -t midnight_blue -d 15000     # Palm & coastline

# Radial patterns
python create_map_poster.py -c "Paris" -C "France" -t pastel_dream -d 10000   # Haussmann boulevards
python create_map_poster.py -c "Moscow" -C "Russia" -t noir -d 12000          # Ring roads

# Organic old cities
python create_map_poster.py -c "Tokyo" -C "Japan" -t japanese_ink -d 15000    # Dense organic streets
python create_map_poster.py -c "Marrakech" -C "Morocco" -t terracotta -d 5000 # Medina maze
python create_map_poster.py -c "Rome" -C "Italy" -t warm_beige -d 8000        # Ancient layout

# Coastal cities
python create_map_poster.py -c "San Francisco" -C "USA" -t sunset -d 10000    # Peninsula grid
python create_map_poster.py -c "Sydney" -C "Australia" -t ocean -d 12000      # Harbor city
python create_map_poster.py -c "Mumbai" -C "India" -t contrast_zones -d 18000 # Coastal peninsula

# River cities
python create_map_poster.py -c "London" -C "UK" -t noir -d 15000              # Thames curves
python create_map_poster.py -c "Budapest" -C "Hungary" -t copper_patina -d 8000  # Danube split

# Override center coordinates
python create_map_poster.py --city "New York" --country "USA" -lat 40.776676 -long -73.971321 -t noir

# List available themes
python create_map_poster.py --list-themes

# Generate posters for every theme
python create_map_poster.py -c "Tokyo" -C "Japan" --all-themes
```

### Distance Guide

| Distance | Best for |
|----------|----------|
| 4000-6000m | Small/dense cities (Venice, Amsterdam center) |
| 8000-12000m | Medium cities, focused downtown (Paris, Barcelona) |
| 15000-20000m | Large metros, full city view (Tokyo, Mumbai) |

## Themes

17 themes available in `themes/` directory:

| Theme | Style |
|-------|-------|
| `gradient_roads` | Smooth gradient shading |
| `contrast_zones` | High contrast urban density |
| `noir` | Pure black background, white roads |
| `midnight_blue` | Navy background with gold roads |
| `blueprint` | Architectural blueprint aesthetic |
| `neon_cyberpunk` | Dark with electric pink/cyan |
| `warm_beige` | Vintage sepia tones |
| `pastel_dream` | Soft muted pastels |
| `japanese_ink` | Minimalist ink wash style |
| `emerald`      | Lush dark green aesthetic |
| `forest` | Deep greens and sage |
| `ocean` | Blues and teals for coastal cities |
| `terracotta` | Mediterranean warmth |
| `sunset` | Warm oranges and pinks |
| `autumn` | Seasonal burnt oranges and reds |
| `copper_patina` | Oxidized copper aesthetic |
| `monochrome_blue` | Single blue color family |

## Output

Posters are saved to `posters/` directory with format:

```text
{city}_{theme}_{YYYYMMDD_HHMMSS}.png
```

## Adding Custom Themes

Create a JSON file in `themes/` directory:

```json
{
  "name": "My Theme",
  "description": "Description of the theme",
  "bg": "#FFFFFF",
  "text": "#000000",
  "gradient_color": "#FFFFFF",
  "water": "#C0C0C0",
  "parks": "#F0F0F0",
  "road_motorway": "#0A0A0A",
  "road_primary": "#1A1A1A",
  "road_secondary": "#2A2A2A",
  "road_tertiary": "#3A3A3A",
  "road_residential": "#4A4A4A",
  "road_default": "#3A3A3A"
}
```

## Project Structure

```text
map_poster/
├── create_map_poster.py    # Main script
├── font_management.py      # Font loading and Google Fonts integration
├── themes/                 # Theme JSON files
├── fonts/                  # Font files
│   ├── Roboto-*.ttf        # Default Roboto fonts
│   └── cache/              # Downloaded Google Fonts (auto-generated)
├── posters/                # Generated posters
└── README.md
```


## Hacker's Guide

Quick reference for contributors who want to extend or modify the script.

### Contributors Guide

- Bug fixes are welcomed
- Don't submit user interface (web/desktop)
- Don't Dockerize for now
- If you vibe code any fix please test it and see before and after version of poster
- Before embarking on a big feature please ask in Discussions/Issue if it will be merged

### Architecture Overview

```text
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│   CLI Parser    │────▶│  Geocoding   │────▶│  Data Fetching  │
│   (argparse)    │     │  (Nominatim) │     │    (OSMnx)      │
└─────────────────┘     └──────────────┘     └─────────────────┘
                                                     │
                        ┌──────────────┐             ▼
                        │    Output    │◀────┌─────────────────┐
                        │  (matplotlib)│     │   Rendering     │
                        └──────────────┘     │  (matplotlib)   │
                                             └─────────────────┘
```

### Key Functions

| Function | Purpose | Modify when... |
|----------|---------|----------------|
| `get_coordinates()` | City → lat/lon via Nominatim | Switching geocoding provider |
| `create_poster()` | Main rendering pipeline | Adding new map layers |
| `get_edge_colors_by_type()` | Road color by OSM highway tag | Changing road styling |
| `get_edge_widths_by_type()` | Road width by importance | Adjusting line weights |
| `create_gradient_fade()` | Top/bottom fade effect | Modifying gradient overlay |
| `load_theme()` | JSON theme → dict | Adding new theme properties |
| `is_latin_script()` | Detects script for typography | Supporting new scripts |
| `load_fonts()` | Load custom/default fonts | Changing font loading logic |

### Rendering Layers (z-order)

```text
z=11  Text labels (city, country, coords)
z=10  Gradient fades (top & bottom)
z=3   Roads (via ox.plot_graph)
z=2   Parks (green polygons)
z=1   Water (blue polygons)
z=0   Background color
```

### OSM Highway Types → Road Hierarchy

```python
# In get_edge_colors_by_type() and get_edge_widths_by_type()
motorway, motorway_link     → Thickest (1.2), darkest
trunk, primary              → Thick (1.0)
secondary                   → Medium (0.8)
tertiary                    → Thin (0.6)
residential, living_street  → Thinnest (0.4), lightest
```

### Typography & Script Detection

The script automatically detects text scripts to apply appropriate typography:

- **Latin scripts** (English, French, Spanish, etc.): Letter spacing applied for elegant "P  A  R  I  S" effect
- **Non-Latin scripts** (Japanese, Arabic, Thai, Korean, etc.): Natural spacing for "東京" (no gaps between characters)

Script detection uses Unicode ranges (U+0000-U+024F for Latin). If >80% of alphabetic characters are Latin, spacing is applied.

### Adding New Features

**New map layer (e.g., railways):**

```python
# In create_poster(), after parks fetch:
try:
    railways = ox.features_from_point(point, tags={'railway': 'rail'}, dist=dist)
except:
    railways = None

# Then plot before roads:
if railways is not None and not railways.empty:
    railways = railways.to_crs(g_proj.graph["crs"])
    railways.plot(ax=ax, color=THEME['railway'], linewidth=0.5, zorder=2.5)
```

**New theme property:**

1. Add to theme JSON: `"railway": "#FF0000"`
2. Use in code: `THEME['railway']`
3. Add fallback in `load_theme()` default dict

### Typography Positioning

All text uses `transform=ax.transAxes` (0-1 normalized coordinates):

```text
y=0.14  City name (spaced letters for Latin scripts)
y=0.125 Decorative line
y=0.10  Country name
y=0.07  Coordinates
y=0.02  Attribution (bottom-right)
```

### Useful OSMnx Patterns

```python
# Get all buildings
buildings = ox.features_from_point(point, tags={'building': True}, dist=dist)

# Get specific amenities
cafes = ox.features_from_point(point, tags={'amenity': 'cafe'}, dist=dist)

# Different network types
G = ox.graph_from_point(point, dist=dist, network_type='drive')  # roads only
G = ox.graph_from_point(point, dist=dist, network_type='bike')   # bike paths
G = ox.graph_from_point(point, dist=dist, network_type='walk')   # pedestrian
```

### Performance Tips

- Large `dist` values (>20km) = slow downloads + memory heavy
- Cache coordinates locally to avoid Nominatim rate limits
- Use `network_type='drive'` instead of `'all'` for faster renders
- Reduce `dpi` from 300 to 150 for quick previews

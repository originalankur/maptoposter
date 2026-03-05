"""
Command-line interface for the maptoposter tool.

Provides the same argparse interface as the original create_map_poster.py.
"""

from __future__ import annotations

import argparse
import sys
import traceback

from lat_lon_parser import parse

from . import constants
from .fonts import load_fonts
from .geocoding import get_coordinates
from .models import Coordinates, PosterConfig
from .output import generate_output_filename
from .rendering import compose_poster
from .theme import get_available_themes, list_themes, load_theme


def print_examples() -> None:
    """Print usage examples."""
    print("""
City Map Poster Generator
=========================

Usage:
  python create_map_poster.py --city <city> --country <country> [options]

Examples:
  # Iconic grid patterns
  python create_map_poster.py -c "New York" -C "USA" -t noir -d 12000           # Manhattan grid
  python create_map_poster.py -c "Barcelona" -C "Spain" -t warm_beige -d 8000   # Eixample district grid

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
  python create_map_poster.py -c "Rome" -C "Italy" -t warm_beige -d 8000        # Ancient street layout

  # Coastal cities
  python create_map_poster.py -c "San Francisco" -C "USA" -t sunset -d 10000    # Peninsula grid
  python create_map_poster.py -c "Sydney" -C "Australia" -t ocean -d 12000      # Harbor city
  python create_map_poster.py -c "Mumbai" -C "India" -t contrast_zones -d 18000 # Coastal peninsula

  # River cities
  python create_map_poster.py -c "London" -C "UK" -t noir -d 15000              # Thames curves
  python create_map_poster.py -c "Budapest" -C "Hungary" -t copper_patina -d 8000  # Danube split

  # List themes
  python create_map_poster.py --list-themes

Options:
  --city, -c        City name (required)
  --country, -C     Country name (required)
  --country-label   Override country text displayed on poster
  --theme, -t       Theme name (default: terracotta)
  --all-themes      Generate posters for all themes
  --distance, -d    Map radius in meters (default: 18000)
  --list-themes     List all available themes

Distance guide:
  4000-6000m   Small/dense cities (Venice, Amsterdam old center)
  8000-12000m  Medium cities, focused downtown (Paris, Barcelona)
  15000-20000m Large metros, full city view (Tokyo, Mumbai)

Available themes can be found in the 'themes/' directory.
Generated posters are saved to 'posters/' directory.
""")


def build_parser() -> argparse.ArgumentParser:
    """
    Build the argument parser with all CLI options.

    Returns:
        Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(
        description="Generate beautiful map posters for any city",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python create_map_poster.py --city "New York" --country "USA"
  python create_map_poster.py --city "New York" --country "USA" -l 40.776676 -73.971321 --theme neon_cyberpunk
  python create_map_poster.py --city Tokyo --country Japan --theme midnight_blue
  python create_map_poster.py --city Paris --country France --theme noir --distance 15000
  python create_map_poster.py --list-themes
        """,
    )

    parser.add_argument("--city", "-c", type=str, help="City name")
    parser.add_argument("--country", "-C", type=str, help="Country name")
    parser.add_argument(
        "--latitude", "-lat", dest="latitude", type=str,
        help="Override latitude center point",
    )
    parser.add_argument(
        "--longitude", "-long", dest="longitude", type=str,
        help="Override longitude center point",
    )
    parser.add_argument(
        "--country-label", dest="country_label", type=str,
        help="Override country text displayed on poster",
    )
    parser.add_argument(
        "--theme", "-t", type=str, default=constants.DEFAULT_THEME,
        help=f"Theme name (default: {constants.DEFAULT_THEME})",
    )
    parser.add_argument(
        "--all-themes", "--All-themes", dest="all_themes", action="store_true",
        help="Generate posters for all themes",
    )
    parser.add_argument(
        "--distance", "-d", type=int, default=constants.DEFAULT_DISTANCE,
        help=f"Map radius in meters (default: {constants.DEFAULT_DISTANCE})",
    )
    parser.add_argument(
        "--width", "-W", type=float, default=constants.DEFAULT_WIDTH,
        help=f"Image width in inches (default: {constants.DEFAULT_WIDTH}, max: {constants.MAX_DIMENSION_INCHES})",
    )
    parser.add_argument(
        "--height", "-H", type=float, default=constants.DEFAULT_HEIGHT,
        help=f"Image height in inches (default: {constants.DEFAULT_HEIGHT}, max: {constants.MAX_DIMENSION_INCHES})",
    )
    parser.add_argument(
        "--list-themes", action="store_true",
        help="List all available themes",
    )
    parser.add_argument(
        "--display-city", "-dc", type=str,
        help="Custom display name for city (for i18n support)",
    )
    parser.add_argument(
        "--display-country", "-dC", type=str,
        help="Custom display name for country (for i18n support)",
    )
    parser.add_argument(
        "--font-family", type=str,
        help='Google Fonts family name (e.g., "Noto Sans JP", "Open Sans"). '
             "If not specified, uses local Roboto fonts.",
    )
    parser.add_argument(
        "--format", "-f", default="png", choices=["png", "svg", "pdf"],
        help="Output format for the poster (default: png)",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """
    CLI entry point.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:])

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    # If no arguments provided, show examples
    if len(sys.argv) == 1 and argv is None:
        print_examples()
        return 0

    # List themes if requested
    if args.list_themes:
        list_themes()
        return 0

    # Validate required arguments
    if not args.city or not args.country:
        print("Error: --city and --country are required.\n")
        print_examples()
        return 1

    # Enforce maximum dimensions
    max_dim = constants.MAX_DIMENSION_INCHES
    if args.width > max_dim:
        print(
            f"\u26a0 Width {args.width} exceeds the maximum allowed limit of "
            f"{max_dim}. It's enforced as max limit {max_dim}."
        )
        args.width = max_dim
    if args.height > max_dim:
        print(
            f"\u26a0 Height {args.height} exceeds the maximum allowed limit of "
            f"{max_dim}. It's enforced as max limit {max_dim}."
        )
        args.height = max_dim

    available_themes = get_available_themes()
    if not available_themes:
        print("No themes found in 'themes/' directory.")
        return 1

    if args.all_themes:
        themes_to_generate = available_themes
    else:
        if args.theme not in available_themes:
            print(f"Error: Theme '{args.theme}' not found.")
            print(f"Available themes: {', '.join(available_themes)}")
            return 1
        themes_to_generate = [args.theme]

    print("=" * 50)
    print("City Map Poster Generator")
    print("=" * 50)

    # Load default fonts (Roboto)
    default_fonts = load_fonts()

    # Load custom fonts if specified
    custom_fonts = None
    if args.font_family:
        custom_fonts = load_fonts(args.font_family)
        if not custom_fonts:
            print(f"\u26a0 Failed to load '{args.font_family}', falling back to Roboto")

    # Get coordinates and generate poster
    try:
        if args.latitude and args.longitude:
            lat = parse(args.latitude)
            lon = parse(args.longitude)
            coords = Coordinates(latitude=lat, longitude=lon)
            print(f"\u2713 Coordinates: {lat}, {lon}")
        else:
            coords = get_coordinates(args.city, args.country)

        for theme_name in themes_to_generate:
            theme = load_theme(theme_name)
            output_file = generate_output_filename(
                args.city, theme_name, args.format
            )

            # Resolve display names
            display_city = args.display_city or args.city
            display_country = args.display_country or args.country_label or args.country

            config = PosterConfig(
                city=args.city,
                country=args.country,
                center=coords,
                dist=args.distance,
                width=args.width,
                height=args.height,
                theme=theme,
                fonts=custom_fonts or default_fonts,
                output_file=output_file,
                output_format=args.format,
                display_city=display_city,
                display_country=display_country,
            )

            compose_poster(config, default_fonts=default_fonts)

        print("\n" + "=" * 50)
        print("\u2713 Poster generation complete!")
        print("=" * 50)
        return 0

    except Exception as e:
        print(f"\n\u2717 Error: {e}")
        traceback.print_exc()
        return 1

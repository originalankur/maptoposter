"""
Output file handling for generated posters.

Handles filename generation and saving matplotlib figures to disk.
"""

from __future__ import annotations

import os
from datetime import datetime

import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from . import constants
from .models import PosterConfig


def generate_output_filename(
    city: str, theme_name: str, output_format: str
) -> str:
    """
    Generate unique output filename with city, theme, and datetime.

    Args:
        city: City name
        theme_name: Theme name
        output_format: File format extension (png, svg, pdf)

    Returns:
        Full path to output file in posters directory
    """
    if not os.path.exists(constants.POSTERS_DIR):
        os.makedirs(constants.POSTERS_DIR)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    city_slug = city.lower().replace(" ", "_")
    ext = output_format.lower()
    filename = f"{city_slug}_{theme_name}_{timestamp}.{ext}"
    return os.path.join(constants.POSTERS_DIR, filename)


def save_poster(fig: Figure, config: PosterConfig) -> None:
    """
    Save a matplotlib figure to disk in the configured format.

    Args:
        fig: Matplotlib figure to save
        config: Poster configuration with output path and format
    """
    print(f"Saving to {config.output_file}...")

    fmt = config.output_format.lower()
    save_kwargs: dict = dict(
        facecolor=config.theme.bg,
        bbox_inches="tight",
        pad_inches=0.05,
    )

    # DPI matters mainly for raster formats
    if fmt == "png":
        save_kwargs["dpi"] = constants.RASTER_DPI

    plt.savefig(config.output_file, format=fmt, **save_kwargs)
    print(f"\u2713 Done! Poster saved as {config.output_file}")

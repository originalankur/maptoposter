"""
Font Management Module - backward-compatible re-export.

Use maptoposter.fonts instead.
"""

from maptoposter.fonts import download_google_font, load_fonts

__all__ = ["load_fonts", "download_google_font"]

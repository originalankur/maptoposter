#!/usr/bin/env python3
"""
City Map Poster Generator

Backward-compatible entry point. Delegates to the maptoposter package.
"""

import sys

from maptoposter.cli import main

if __name__ == "__main__":
    sys.exit(main())

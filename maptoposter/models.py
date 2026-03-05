"""
Data models for the maptoposter package.

All models are frozen dataclasses to prevent accidental mutation.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import constants


@dataclass(frozen=True)
class Coordinates:
    """Geographic coordinates for the map center."""

    latitude: float
    longitude: float

    def format_display(self) -> str:
        """Format as '12.9716° N / 77.5946° E' with correct hemisphere indicators."""
        lat_dir = "N" if self.latitude >= 0 else "S"
        lon_dir = "E" if self.longitude >= 0 else "W"
        prec = constants.COORD_DECIMAL_PLACES
        return f"{abs(self.latitude):.{prec}f}\u00b0 {lat_dir} / {abs(self.longitude):.{prec}f}\u00b0 {lon_dir}"

    def as_tuple(self) -> tuple[float, float]:
        """Return as (latitude, longitude) tuple for compatibility with osmnx/geopy."""
        return (self.latitude, self.longitude)


@dataclass(frozen=True)
class RoadColors:
    """Color assignments for each road tier."""

    motorway: str
    primary: str
    secondary: str
    tertiary: str
    residential: str
    default: str


@dataclass(frozen=True)
class Theme:
    """Complete visual theme loaded from a JSON file."""

    name: str
    description: str
    bg: str
    text: str
    gradient_color: str
    water: str
    parks: str
    roads: RoadColors

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> Theme:
        """Construct from the flat JSON dict the theme files use."""
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            bg=data["bg"],
            text=data["text"],
            gradient_color=data["gradient_color"],
            water=data["water"],
            parks=data["parks"],
            roads=RoadColors(
                motorway=data["road_motorway"],
                primary=data["road_primary"],
                secondary=data["road_secondary"],
                tertiary=data["road_tertiary"],
                residential=data["road_residential"],
                default=data["road_default"],
            ),
        )


@dataclass(frozen=True)
class FontSet:
    """Paths to bold/regular/light font files."""

    bold: str
    regular: str
    light: str

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> FontSet:
        """Construct from a dict with 'bold', 'regular', 'light' keys."""
        return cls(
            bold=data["bold"],
            regular=data["regular"],
            light=data["light"],
        )


@dataclass(frozen=True)
class PosterConfig:
    """All parameters needed to generate a single poster."""

    city: str
    country: str
    center: Coordinates
    dist: int
    width: float
    height: float
    theme: Theme
    fonts: FontSet | None
    output_file: str
    output_format: str
    display_city: str
    display_country: str

"""Shared test fixtures for maptoposter tests."""

from __future__ import annotations

import json

import pytest

from maptoposter.models import Coordinates, PosterConfig, Theme


SAMPLE_THEME_DATA = {
    "name": "Test Theme",
    "description": "A test theme",
    "bg": "#FFFFFF",
    "text": "#000000",
    "gradient_color": "#FFFFFF",
    "water": "#0000FF",
    "parks": "#00FF00",
    "road_motorway": "#FF0000",
    "road_primary": "#CC0000",
    "road_secondary": "#990000",
    "road_tertiary": "#660000",
    "road_residential": "#330000",
    "road_default": "#111111",
}


@pytest.fixture
def sample_theme_data() -> dict[str, str]:
    """Raw theme dict as loaded from JSON."""
    return SAMPLE_THEME_DATA.copy()


@pytest.fixture
def sample_theme() -> Theme:
    """A Theme dataclass for testing."""
    return Theme.from_dict(SAMPLE_THEME_DATA)


@pytest.fixture
def sample_coords() -> Coordinates:
    """Coordinates for Paris, France."""
    return Coordinates(latitude=48.8566, longitude=2.3522)


@pytest.fixture
def sample_config(sample_theme: Theme, sample_coords: Coordinates, tmp_path) -> PosterConfig:
    """A minimal PosterConfig for testing."""
    return PosterConfig(
        city="Paris",
        country="France",
        center=sample_coords,
        dist=18000,
        width=12.0,
        height=16.0,
        theme=sample_theme,
        fonts=None,
        output_file=str(tmp_path / "test_poster.png"),
        output_format="png",
        display_city="Paris",
        display_country="France",
    )


@pytest.fixture
def themes_dir(tmp_path) -> str:
    """A temporary themes directory with test theme files."""
    themes = tmp_path / "themes"
    themes.mkdir()

    for name in ["alpha", "beta"]:
        theme_file = themes / f"{name}.json"
        data = SAMPLE_THEME_DATA.copy()
        data["name"] = name.title()
        data["description"] = f"The {name} theme"
        theme_file.write_text(json.dumps(data))

    return str(themes)

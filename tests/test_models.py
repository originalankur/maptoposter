"""Tests for maptoposter.models."""

from __future__ import annotations

import pytest

from maptoposter.models import Coordinates, FontSet, RoadColors, Theme


class TestCoordinates:
    def test_north_east(self):
        c = Coordinates(latitude=48.8566, longitude=2.3522)
        assert c.format_display() == "48.8566\u00b0 N / 2.3522\u00b0 E"

    def test_south_west(self):
        c = Coordinates(latitude=-33.8688, longitude=-151.2093)
        assert c.format_display() == "33.8688\u00b0 S / 151.2093\u00b0 W"

    def test_south_east(self):
        c = Coordinates(latitude=-6.2088, longitude=106.8456)
        assert c.format_display() == "6.2088\u00b0 S / 106.8456\u00b0 E"

    def test_north_west(self):
        c = Coordinates(latitude=40.7128, longitude=-74.0060)
        assert c.format_display() == "40.7128\u00b0 N / 74.0060\u00b0 W"

    def test_zero_coords(self):
        c = Coordinates(latitude=0.0, longitude=0.0)
        assert "N" in c.format_display()
        assert "E" in c.format_display()

    def test_as_tuple(self):
        c = Coordinates(latitude=48.8566, longitude=2.3522)
        assert c.as_tuple() == (48.8566, 2.3522)

    def test_frozen(self):
        c = Coordinates(latitude=48.8566, longitude=2.3522)
        with pytest.raises(AttributeError):
            c.latitude = 0.0  # type: ignore[misc]


class TestRoadColors:
    def test_creation(self):
        rc = RoadColors(
            motorway="#FF0000", primary="#CC0000", secondary="#990000",
            tertiary="#660000", residential="#330000", default="#111111",
        )
        assert rc.motorway == "#FF0000"
        assert rc.default == "#111111"


class TestTheme:
    def test_from_dict(self, sample_theme_data):
        theme = Theme.from_dict(sample_theme_data)
        assert theme.name == "Test Theme"
        assert theme.bg == "#FFFFFF"
        assert theme.roads.motorway == "#FF0000"
        assert theme.roads.default == "#111111"

    def test_from_dict_missing_description(self, sample_theme_data):
        del sample_theme_data["description"]
        theme = Theme.from_dict(sample_theme_data)
        assert theme.description == ""

    def test_from_dict_missing_key_raises(self, sample_theme_data):
        del sample_theme_data["bg"]
        with pytest.raises(KeyError):
            Theme.from_dict(sample_theme_data)

    def test_frozen(self, sample_theme):
        with pytest.raises(AttributeError):
            sample_theme.bg = "#000000"  # type: ignore[misc]


class TestFontSet:
    def test_from_dict(self):
        data = {"bold": "/path/bold.ttf", "regular": "/path/regular.ttf", "light": "/path/light.ttf"}
        fs = FontSet.from_dict(data)
        assert fs.bold == "/path/bold.ttf"
        assert fs.regular == "/path/regular.ttf"
        assert fs.light == "/path/light.ttf"

    def test_from_dict_missing_key(self):
        with pytest.raises(KeyError):
            FontSet.from_dict({"bold": "x", "regular": "y"})


class TestPosterConfig:
    def test_creation(self, sample_config):
        assert sample_config.city == "Paris"
        assert sample_config.center.latitude == 48.8566
        assert sample_config.theme.name == "Test Theme"
        assert sample_config.output_format == "png"

"""Tests for maptoposter.text."""

from __future__ import annotations

from maptoposter.text import (
    compute_city_font_size,
    format_city_display,
    is_latin_script,
    make_font,
)
from maptoposter.models import FontSet


class TestIsLatinScript:
    def test_english(self):
        assert is_latin_script("Paris") is True

    def test_french_accents(self):
        assert is_latin_script("Montréal") is True

    def test_german(self):
        assert is_latin_script("München") is True

    def test_japanese(self):
        assert is_latin_script("東京") is False

    def test_arabic(self):
        assert is_latin_script("القاهرة") is False

    def test_korean(self):
        assert is_latin_script("서울") is False

    def test_hindi(self):
        assert is_latin_script("मुंबई") is False

    def test_empty_string(self):
        assert is_latin_script("") is True

    def test_numbers_only(self):
        assert is_latin_script("12345") is True

    def test_mixed_mostly_latin(self):
        # More than 80% latin
        assert is_latin_script("Paris 東") is True

    def test_mixed_mostly_nonlatin(self):
        assert is_latin_script("東京 P") is False


class TestFormatCityDisplay:
    def test_latin_city(self):
        result = format_city_display("Paris")
        assert result == "P  A  R  I  S"

    def test_latin_lowercase(self):
        result = format_city_display("london")
        assert result == "L  O  N  D  O  N"

    def test_nonlatin_city(self):
        result = format_city_display("東京")
        assert result == "東京"

    def test_city_with_spaces(self):
        result = format_city_display("New York")
        assert "N  E  W" in result


class TestComputeCityFontSize:
    def test_short_name(self):
        size = compute_city_font_size("Paris", 60, 1.0)
        assert size == 60.0

    def test_long_name_reduced(self):
        size = compute_city_font_size("San Francisco Bay", 60, 1.0)
        assert size < 60.0

    def test_scale_factor(self):
        size_small = compute_city_font_size("Paris", 60, 0.5)
        size_large = compute_city_font_size("Paris", 60, 2.0)
        assert size_large > size_small

    def test_very_long_name_has_minimum(self):
        size = compute_city_font_size("A" * 100, 60, 1.0)
        assert size >= 10.0  # Minimum scale factor


class TestMakeFont:
    def test_with_none_fonts_returns_monospace(self):
        fp = make_font(None, "bold", 24.0)
        # FontProperties with family="monospace" created
        assert fp.get_size() == 24.0

    def test_with_font_set(self, tmp_path):
        # Create dummy font files
        bold = tmp_path / "bold.ttf"
        regular = tmp_path / "regular.ttf"
        light = tmp_path / "light.ttf"
        for f in [bold, regular, light]:
            f.write_bytes(b"")  # Empty file, enough for path test

        fs = FontSet(bold=str(bold), regular=str(regular), light=str(light))
        fp = make_font(fs, "bold", 16.0)
        assert fp.get_size() == 16.0

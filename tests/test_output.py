"""Tests for maptoposter.output."""

from __future__ import annotations

import re
from unittest.mock import patch

from maptoposter.output import generate_output_filename


class TestGenerateOutputFilename:
    def test_format_png(self, tmp_path):
        with patch("maptoposter.output.constants") as mock_constants:
            mock_constants.POSTERS_DIR = str(tmp_path / "posters")
            result = generate_output_filename("Paris", "noir", "png")
            assert result.endswith(".png")
            assert "paris" in result
            assert "noir" in result

    def test_format_svg(self, tmp_path):
        with patch("maptoposter.output.constants") as mock_constants:
            mock_constants.POSTERS_DIR = str(tmp_path / "posters")
            result = generate_output_filename("London", "ocean", "svg")
            assert result.endswith(".svg")

    def test_city_with_spaces(self, tmp_path):
        with patch("maptoposter.output.constants") as mock_constants:
            mock_constants.POSTERS_DIR = str(tmp_path / "posters")
            result = generate_output_filename("New York", "noir", "png")
            assert "new_york" in result

    def test_creates_directory(self, tmp_path):
        posters_dir = tmp_path / "new_posters"
        with patch("maptoposter.output.constants") as mock_constants:
            mock_constants.POSTERS_DIR = str(posters_dir)
            generate_output_filename("Paris", "noir", "png")
            assert posters_dir.exists()

    def test_timestamp_in_filename(self, tmp_path):
        with patch("maptoposter.output.constants") as mock_constants:
            mock_constants.POSTERS_DIR = str(tmp_path / "posters")
            result = generate_output_filename("Paris", "noir", "png")
            # Should contain YYYYMMDD_HHMMSS pattern
            assert re.search(r"\d{8}_\d{6}", result)

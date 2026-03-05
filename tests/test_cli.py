"""Tests for maptoposter.cli."""

from __future__ import annotations

import pytest

from maptoposter.cli import build_parser, main


class TestBuildParser:
    def test_all_args_present(self):
        parser = build_parser()
        # Parse with all required args
        args = parser.parse_args(["--city", "Paris", "--country", "France"])
        assert args.city == "Paris"
        assert args.country == "France"

    def test_short_flags(self):
        parser = build_parser()
        args = parser.parse_args(["-c", "Tokyo", "-C", "Japan", "-t", "noir"])
        assert args.city == "Tokyo"
        assert args.country == "Japan"
        assert args.theme == "noir"

    def test_defaults(self):
        parser = build_parser()
        args = parser.parse_args(["-c", "X", "-C", "Y"])
        assert args.theme == "terracotta"
        assert args.distance == 18000
        assert args.width == 12.0
        assert args.height == 16.0
        assert args.format == "png"

    def test_all_themes_flag(self):
        parser = build_parser()
        args = parser.parse_args(["-c", "X", "-C", "Y", "--all-themes"])
        assert args.all_themes is True

    def test_list_themes_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--list-themes"])
        assert args.list_themes is True

    def test_display_city_and_country(self):
        parser = build_parser()
        args = parser.parse_args([
            "-c", "Tokyo", "-C", "Japan",
            "-dc", "東京", "-dC", "日本",
        ])
        assert args.display_city == "東京"
        assert args.display_country == "日本"

    def test_font_family(self):
        parser = build_parser()
        args = parser.parse_args(["-c", "X", "-C", "Y", "--font-family", "Noto Sans JP"])
        assert args.font_family == "Noto Sans JP"

    def test_format_choices(self):
        parser = build_parser()
        for fmt in ["png", "svg", "pdf"]:
            args = parser.parse_args(["-c", "X", "-C", "Y", "-f", fmt])
            assert args.format == fmt

    def test_invalid_format(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["-c", "X", "-C", "Y", "-f", "bmp"])

    def test_latitude_longitude(self):
        parser = build_parser()
        args = parser.parse_args([
            "-c", "X", "-C", "Y",
            "-lat", "40.7128", "-long", "-74.0060",
        ])
        assert args.latitude == "40.7128"
        assert args.longitude == "-74.0060"


class TestMain:
    def test_list_themes_returns_0(self):
        result = main(["--list-themes"])
        assert result == 0

    def test_missing_city_returns_1(self):
        result = main(["--country", "France"])
        assert result == 1

    def test_missing_country_returns_1(self):
        result = main(["--city", "Paris"])
        assert result == 1

    def test_invalid_theme_returns_1(self):
        result = main(["--city", "Paris", "--country", "France", "--theme", "nonexistent_theme_xyz"])
        assert result == 1

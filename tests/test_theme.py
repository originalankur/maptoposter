"""Tests for maptoposter.theme."""

from __future__ import annotations

from pathlib import Path

from maptoposter.theme import get_available_themes, list_themes, load_theme


class TestGetAvailableThemes:
    def test_returns_sorted_list(self, themes_dir):
        themes = get_available_themes(Path(themes_dir))
        assert themes == ["alpha", "beta"]

    def test_empty_dir(self, tmp_path):
        empty = tmp_path / "empty_themes"
        empty.mkdir()
        themes = get_available_themes(empty)
        assert themes == []

    def test_nonexistent_dir_creates_it(self, tmp_path):
        new_dir = tmp_path / "new_themes"
        themes = get_available_themes(new_dir)
        assert themes == []
        assert new_dir.exists()

    def test_ignores_non_json(self, tmp_path):
        themes = tmp_path / "themes"
        themes.mkdir()
        (themes / "readme.txt").write_text("not a theme")
        (themes / "test.json").write_text('{"name": "Test"}')
        result = get_available_themes(themes)
        assert result == ["test"]


class TestLoadTheme:
    def test_loads_valid_theme(self, themes_dir):
        theme = load_theme("alpha", Path(themes_dir))
        assert theme.name == "Alpha"

    def test_missing_theme_returns_fallback(self, tmp_path):
        theme = load_theme("nonexistent", tmp_path)
        assert theme.name == "Terracotta"

    def test_theme_has_road_colors(self, themes_dir):
        theme = load_theme("alpha", Path(themes_dir))
        assert theme.roads.motorway == "#FF0000"


class TestListThemes:
    def test_prints_themes(self, themes_dir, capsys):
        list_themes(Path(themes_dir))
        captured = capsys.readouterr()
        assert "alpha" in captured.out
        assert "beta" in captured.out

    def test_empty_dir(self, tmp_path, capsys):
        empty = tmp_path / "empty"
        empty.mkdir()
        list_themes(empty)
        captured = capsys.readouterr()
        assert "No themes found" in captured.out

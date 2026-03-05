"""Tests for maptoposter.cache."""

from __future__ import annotations

from maptoposter.cache import cache_get, cache_set


class TestCache:
    def test_round_trip(self, tmp_path):
        cache_set("test_key", {"data": 42}, cache_dir=tmp_path)
        result = cache_get("test_key", cache_dir=tmp_path)
        assert result == {"data": 42}

    def test_missing_key_returns_none(self, tmp_path):
        result = cache_get("nonexistent", cache_dir=tmp_path)
        assert result is None

    def test_overwrite(self, tmp_path):
        cache_set("key", "first", cache_dir=tmp_path)
        cache_set("key", "second", cache_dir=tmp_path)
        assert cache_get("key", cache_dir=tmp_path) == "second"

    def test_complex_objects(self, tmp_path):
        data = [1, 2, {"nested": True}]
        cache_set("complex", data, cache_dir=tmp_path)
        assert cache_get("complex", cache_dir=tmp_path) == data

    def test_cache_dir_created_if_missing(self, tmp_path):
        new_dir = tmp_path / "new_cache"
        cache_set("key", "value", cache_dir=new_dir)
        assert new_dir.exists()
        assert cache_get("key", cache_dir=new_dir) == "value"

    def test_key_with_path_separators(self, tmp_path):
        cache_set("a/b/c", "safe", cache_dir=tmp_path)
        assert cache_get("a/b/c", cache_dir=tmp_path) == "safe"

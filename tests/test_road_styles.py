"""Tests for maptoposter.road_styles."""

from __future__ import annotations

import networkx as nx
import pytest

from maptoposter.models import RoadColors
from maptoposter.road_styles import classify_highway, compute_edge_styles


class TestClassifyHighway:
    def test_motorway(self):
        assert classify_highway("motorway") == "motorway"

    def test_motorway_link(self):
        assert classify_highway("motorway_link") == "motorway"

    def test_primary(self):
        assert classify_highway("primary") == "primary"

    def test_trunk(self):
        assert classify_highway("trunk") == "primary"

    def test_secondary(self):
        assert classify_highway("secondary") == "secondary"

    def test_tertiary(self):
        assert classify_highway("tertiary") == "tertiary"

    def test_residential(self):
        assert classify_highway("residential") == "residential"

    def test_living_street(self):
        assert classify_highway("living_street") == "residential"

    def test_unknown(self):
        assert classify_highway("footway") == "default"

    def test_list_input(self):
        assert classify_highway(["motorway", "trunk"]) == "motorway"

    def test_empty_list(self):
        assert classify_highway([]) == "residential"  # unclassified maps to residential


class TestComputeEdgeStyles:
    def _make_graph(self, highway_types: list[str]) -> nx.MultiDiGraph:
        g = nx.MultiDiGraph()
        for i, hw in enumerate(highway_types):
            g.add_edge(i, i + 1, highway=hw)
        return g

    @pytest.fixture
    def road_colors(self) -> RoadColors:
        return RoadColors(
            motorway="#M", primary="#P", secondary="#S",
            tertiary="#T", residential="#R", default="#D",
        )

    def test_single_motorway(self, road_colors):
        g = self._make_graph(["motorway"])
        styles = compute_edge_styles(g, road_colors)
        assert styles.colors == ["#M"]
        assert styles.widths == [1.2]

    def test_mixed_types(self, road_colors):
        g = self._make_graph(["motorway", "residential", "secondary"])
        styles = compute_edge_styles(g, road_colors)
        assert len(styles.colors) == 3
        assert len(styles.widths) == 3
        assert styles.colors[0] == "#M"
        assert styles.colors[1] == "#R"
        assert styles.colors[2] == "#S"

    def test_unknown_type_gets_default(self, road_colors):
        g = self._make_graph(["footway"])
        styles = compute_edge_styles(g, road_colors)
        assert styles.colors == ["#D"]
        assert styles.widths == [0.4]

    def test_empty_graph(self, road_colors):
        g = nx.MultiDiGraph()
        styles = compute_edge_styles(g, road_colors)
        assert styles.colors == []
        assert styles.widths == []

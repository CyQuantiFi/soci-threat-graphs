"""
Unit tests for the atlas importer.

Drop into: backend/tests/test_atlas_importer.py
Run with: pytest backend/tests/test_atlas_importer.py
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock

import pytest

# Adjust imports
from ..parsers.atlas_yaml_parser import parse_yaml_file
from ..services.soci_atlas_importer import SociAtlasImporter


SAMPLE = Path(__file__).resolve().parents[2] / "scenarios" / "water" / "WAT-001-scada-engineering-workstation-pivot.yaml"
SCHEMA = Path(__file__).resolve().parents[2] / "schema" / "scenario.schema.json"


@pytest.mark.asyncio
async def test_imports_seed_scenario(monkeypatch):
    atlas = parse_yaml_file(SAMPLE, schema_path=SCHEMA)
    assert atlas.id == "WAT-001"
    assert atlas.sector == "water"
    assert len(atlas.nodes) == 5
    assert any(not n.scannable for n in atlas.nodes), "WAT-001 must carry unscannable nodes"

    graphs = AsyncMock()
    graphs.create_graph.return_value = "graph-uuid"
    graphs.add_node.side_effect = [f"n{i}" for i in range(len(atlas.nodes))]
    graphs.add_edge.side_effect = [f"e{i}" for i in range(len(atlas.edges))]

    scenarios = AsyncMock()
    scenarios.create_fair_scenario.return_value = "fair-uuid"

    markets = AsyncMock()
    markets.suggest_market_for_edge.return_value = "market-uuid"

    importer = SociAtlasImporter(graphs=graphs, scenarios=scenarios, markets=markets)
    result = await importer.import_scenario(project_id="proj-1", atlas=atlas)

    assert result.graph_id == "graph-uuid"
    assert result.fair_scenario_id == "fair-uuid"
    assert result.node_count == len(atlas.nodes)
    assert result.edge_count == len(atlas.edges)
    assert len(result.suggested_market_ids) > 0, "should suggest markets for unscannable edges"
    graphs.create_graph.assert_awaited_once()
    scenarios.create_fair_scenario.assert_awaited_once()

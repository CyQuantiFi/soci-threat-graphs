"""
SOCI Threat Atlas importer service.

Translates AtlasScenario into CyQuantiFi internal graph + FAIR scenario
entities, scoped to a user's project/org. Pure orchestration: relies on the
existing GraphService, ScenarioService, and FAIR engine via dependency
injection so this file does not need to know their internals.

Drop into: backend/src/services/soci_atlas_importer.py
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

from .atlas_yaml_parser import AtlasScenario, AtlasNode, AtlasEdge  # adjust import path

log = logging.getLogger(__name__)


class GraphServiceProto(Protocol):
    async def create_graph(self, project_id: str, name: str, description: str) -> str: ...
    async def add_node(self, graph_id: str, **fields) -> str: ...
    async def add_edge(self, graph_id: str, from_id: str, to_id: str, **fields) -> str: ...


class ScenarioServiceProto(Protocol):
    async def create_fair_scenario(
        self,
        project_id: str,
        graph_id: str,
        title: str,
        annual_frequency: tuple[float, float, float],
        primary_response: tuple[int, int, int],
        secondary_response: tuple[int, int, int],
        currency: str,
        metadata: dict,
    ) -> str: ...


class MarketServiceProto(Protocol):
    async def suggest_market_for_edge(
        self,
        scenario_id: str,
        edge_id: str,
        prior: tuple[float, float, float],
    ) -> str | None: ...


@dataclass
class ImportResult:
    scenario_id: str
    graph_id: str
    fair_scenario_id: str
    suggested_market_ids: list[str]
    node_count: int
    edge_count: int


class SociAtlasImporter:
    """Compose atlas YAML into a CyQuantiFi graph + FAIR scenario.

    The bridge is intentionally one-way: atlas YAML is the prior, CyQuantiFi
    is where the posterior lives. We do not push posterior data back to the
    atlas at import time; that flow (if ever enabled) is a separate quarterly
    aggregation job.
    """

    def __init__(
        self,
        graphs: GraphServiceProto,
        scenarios: ScenarioServiceProto,
        markets: MarketServiceProto | None = None,
    ):
        self.graphs = graphs
        self.scenarios = scenarios
        self.markets = markets

    async def import_scenario(
        self,
        project_id: str,
        atlas: AtlasScenario,
        suggest_markets_for_unscannable_edges: bool = True,
    ) -> ImportResult:
        graph_id = await self.graphs.create_graph(
            project_id=project_id,
            name=f"{atlas.id} · {atlas.title}",
            description=(
                f"Imported from SOCI Threat Atlas {atlas.id} v{atlas.version}. "
                f"Sector: {atlas.sector}. Adjust nodes to match your environment."
            ),
        )

        node_id_map: dict[str, str] = {}
        for n in atlas.nodes:
            cy_id = await self._add_node(graph_id, n)
            node_id_map[n.id] = cy_id

        added_edges: list[tuple[str, str, AtlasEdge]] = []
        for e in atlas.edges:
            from_id = node_id_map.get(e.from_) or e.from_  # 'external' passes through
            to_id = node_id_map[e.to]
            edge_id = await self.graphs.add_edge(
                graph_id=graph_id,
                from_id=from_id,
                to_id=to_id,
                mitre_technique=e.technique,
                detection_difficulty=e.detection_difficulty,
                notes=e.notes,
                source=f"atlas:{atlas.id}",
            )
            added_edges.append((edge_id, to_id, e))

        fair_id = await self.scenarios.create_fair_scenario(
            project_id=project_id,
            graph_id=graph_id,
            title=atlas.title,
            annual_frequency=(
                atlas.annual_frequency.min,
                atlas.annual_frequency.mode,
                atlas.annual_frequency.max,
            ),
            primary_response=(
                atlas.primary_response.min,
                atlas.primary_response.mode,
                atlas.primary_response.max,
            ),
            secondary_response=(
                atlas.secondary_response.min,
                atlas.secondary_response.mode,
                atlas.secondary_response.max,
            ),
            currency=atlas.currency,
            metadata={
                "atlas_id": atlas.id,
                "atlas_version": atlas.version,
                "atlas_last_reviewed": atlas.last_reviewed,
                "atlas_references": atlas.references,
                "mitre_tactics": atlas.mitre_tactics,
                "mitre_techniques": atlas.mitre_techniques,
                "suggested_controls": atlas.controls_suggested,
                "summary": atlas.summary,
            },
        )

        market_ids: list[str] = []
        if suggest_markets_for_unscannable_edges and self.markets:
            unscannable_node_ids = {
                node_id_map[n.id] for n in atlas.nodes if not n.scannable
            }
            for edge_id, to_id, edge in added_edges:
                if to_id in unscannable_node_ids:
                    # Default Beta-PERT on edge probability — analyst can refine
                    market_id = await self.markets.suggest_market_for_edge(
                        scenario_id=fair_id,
                        edge_id=edge_id,
                        prior=(0.05, 0.15, 0.40),
                    )
                    if market_id:
                        market_ids.append(market_id)

        return ImportResult(
            scenario_id=atlas.id,
            graph_id=graph_id,
            fair_scenario_id=fair_id,
            suggested_market_ids=market_ids,
            node_count=len(atlas.nodes),
            edge_count=len(atlas.edges),
        )

    async def _add_node(self, graph_id: str, n: AtlasNode) -> str:
        return await self.graphs.add_node(
            graph_id=graph_id,
            atlas_id=n.id,
            name=n.id.replace("_", " ").title(),
            description=n.description,
            asset_type=n.type,
            scannable=n.scannable,
            reason_unscannable=n.reason_unscannable,
            criticality=n.criticality,
            consequence_type=n.consequence_type,
            source="atlas",
        )

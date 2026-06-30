"""
FastAPI route: import a SOCI Threat Atlas scenario into the caller's project.

Drop into: backend/src/routes/scenario_import.py
"""
from __future__ import annotations

import logging
from pathlib import Path

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

# Adjust these imports to the main project's actual paths.
from ..parsers.atlas_yaml_parser import parse_yaml_string, AtlasParseError
from ..services.soci_atlas_importer import SociAtlasImporter, ImportResult
from ..deps import (
    require_current_user,
    require_org_scope,
    get_atlas_importer,  # wires the importer with GraphService, ScenarioService, MarketService
)

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/scenarios", tags=["scenarios"])

ATLAS_RAW_BASE = (
    "https://raw.githubusercontent.com/cyquantifi/soci-threat-graphs/{ref}/scenarios"
)

# Map atlas IDs to sector folders. In production this is fetched and cached
# from the atlas repo's manifest; here we hardcode the prefix mapping.
SECTOR_PREFIX = {
    "WAT": "water",
    "ELE": "electricity",
    "GAS": "gas",
    "POR": "ports",
    "AVI": "aviation",
    "HLT": "healthcare",
}


class ImportByIdRequest(BaseModel):
    atlas_id: str = Field(..., pattern=r"^(WAT|ELE|GAS|POR|AVI|HLT)-[0-9]{3}$")
    project_id: str
    ref: str = Field("main", description="Atlas git ref (branch, tag, or commit)")
    suggest_markets: bool = True


class ImportByYamlRequest(BaseModel):
    yaml_text: str = Field(..., min_length=200)
    project_id: str
    suggest_markets: bool = True


class ImportResponse(BaseModel):
    atlas_id: str
    graph_id: str
    fair_scenario_id: str
    suggested_market_ids: list[str]
    node_count: int
    edge_count: int


@router.post("/import", response_model=ImportResponse)
async def import_scenario_by_id(
    payload: ImportByIdRequest,
    user=Depends(require_current_user),
    org=Depends(require_org_scope),
    importer: SociAtlasImporter = Depends(get_atlas_importer),
) -> ImportResponse:
    prefix = payload.atlas_id.split("-")[0]
    sector = SECTOR_PREFIX[prefix]
    base = ATLAS_RAW_BASE.format(ref=payload.ref)

    # Atlas filenames follow <ID>-<slug>.yaml. We accept any slug — fetch the
    # GitHub raw directory listing via the contents API and find the match.
    async with httpx.AsyncClient(timeout=10) as client:
        listing = await client.get(
            f"https://api.github.com/repos/cyquantifi/soci-threat-graphs/contents/"
            f"scenarios/{sector}?ref={payload.ref}"
        )
        if listing.status_code != 200:
            raise HTTPException(
                status.HTTP_502_BAD_GATEWAY,
                detail=f"Atlas listing unavailable: {listing.status_code}",
            )
        match = next(
            (
                item
                for item in listing.json()
                if item["name"].startswith(payload.atlas_id + "-")
            ),
            None,
        )
        if not match:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, detail=f"Scenario {payload.atlas_id} not found at ref {payload.ref}"
            )
        fetch = await client.get(f"{base}/{sector}/{match['name']}")
        if fetch.status_code != 200:
            raise HTTPException(
                status.HTTP_502_BAD_GATEWAY,
                detail=f"Could not fetch scenario YAML: {fetch.status_code}",
            )
        yaml_text = fetch.text

    return await _do_import(
        yaml_text=yaml_text,
        project_id=payload.project_id,
        suggest_markets=payload.suggest_markets,
        importer=importer,
    )


@router.post("/import/raw", response_model=ImportResponse)
async def import_scenario_by_yaml(
    payload: ImportByYamlRequest,
    user=Depends(require_current_user),
    org=Depends(require_org_scope),
    importer: SociAtlasImporter = Depends(get_atlas_importer),
) -> ImportResponse:
    return await _do_import(
        yaml_text=payload.yaml_text,
        project_id=payload.project_id,
        suggest_markets=payload.suggest_markets,
        importer=importer,
    )


async def _do_import(
    yaml_text: str,
    project_id: str,
    suggest_markets: bool,
    importer: SociAtlasImporter,
) -> ImportResponse:
    # The schema file is vendored in the backend image at deploy time.
    schema_path = Path(__file__).resolve().parent.parent / "vendor" / "atlas_scenario.schema.json"
    try:
        atlas = parse_yaml_string(yaml_text, schema_path=schema_path)
    except AtlasParseError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    result: ImportResult = await importer.import_scenario(
        project_id=project_id,
        atlas=atlas,
        suggest_markets_for_unscannable_edges=suggest_markets,
    )
    return ImportResponse(
        atlas_id=atlas.id,
        graph_id=result.graph_id,
        fair_scenario_id=result.fair_scenario_id,
        suggested_market_ids=result.suggested_market_ids,
        node_count=result.node_count,
        edge_count=result.edge_count,
    )

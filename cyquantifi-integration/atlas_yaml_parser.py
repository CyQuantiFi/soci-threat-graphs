"""
SOCI Threat Atlas YAML parser.

Reads a scenario YAML file (or string) and returns a typed AtlasScenario
ready for the importer service. Validates against the JSON Schema bundled
with the atlas.

Drop into: backend/src/parsers/atlas_yaml_parser.py
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

log = logging.getLogger(__name__)

# When deployed, fetch from the atlas repo at a pinned ref. For local dev
# this can point at a checked-out copy.
ATLAS_SCHEMA_URL = (
    "https://raw.githubusercontent.com/cyquantifi/soci-threat-graphs/main/"
    "schema/scenario.schema.json"
)


@dataclass
class AtlasNode:
    id: str
    type: str
    description: str
    scannable: bool
    criticality: str
    reason_unscannable: str | None = None
    consequence_type: str | None = None


@dataclass
class AtlasEdge:
    from_: str
    to: str
    technique: str
    detection_difficulty: str
    notes: str | None = None


@dataclass
class BetaPert:
    min: float
    mode: float
    max: float
    notes: str | None = None


@dataclass
class AtlasScenario:
    id: str
    title: str
    version: str
    sector: str
    soci_asset_class: str
    summary: str
    mitre_tactics: list[str]
    mitre_techniques: list[dict[str, str]]
    nodes: list[AtlasNode]
    edges: list[AtlasEdge]
    annual_frequency: BetaPert
    primary_response: BetaPert
    secondary_response: BetaPert
    currency: str
    references: list[str]
    controls_suggested: list[dict[str, str]] = field(default_factory=list)
    last_reviewed: str = ""


class AtlasParseError(ValueError):
    """Raised when a YAML cannot be parsed or fails schema validation."""


def _load_schema(schema_path: Path | None = None) -> dict[str, Any]:
    if schema_path and schema_path.exists():
        return json.loads(schema_path.read_text())
    raise AtlasParseError(
        "Schema not provided. Pass schema_path or vendor the schema with the importer."
    )


def parse_yaml_string(
    text: str, schema_path: Path | None = None
) -> AtlasScenario:
    try:
        doc = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise AtlasParseError(f"YAML parse failed: {exc}") from exc

    if not isinstance(doc, dict):
        raise AtlasParseError("Top-level YAML must be a mapping")

    schema = _load_schema(schema_path)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(doc), key=lambda e: list(e.absolute_path))
    if errors:
        first = errors[0]
        loc = "/".join(str(p) for p in first.absolute_path) or "<root>"
        raise AtlasParseError(f"Schema validation failed at {loc}: {first.message}")

    return _to_scenario(doc)


def parse_yaml_file(
    path: Path, schema_path: Path | None = None
) -> AtlasScenario:
    return parse_yaml_string(path.read_text(), schema_path=schema_path)


def _to_scenario(doc: dict[str, Any]) -> AtlasScenario:
    nodes = [
        AtlasNode(
            id=n["id"],
            type=n["type"],
            description=n["description"],
            scannable=n["scannable"],
            criticality=n["criticality"],
            reason_unscannable=n.get("reason_unscannable"),
            consequence_type=n.get("consequence_type"),
        )
        for n in doc["nodes"]
    ]
    edges = [
        AtlasEdge(
            from_=e["from"],
            to=e["to"],
            technique=e["technique"],
            detection_difficulty=e["detection_difficulty"],
            notes=e.get("notes"),
        )
        for e in doc["edges"]
    ]
    lik = doc["likelihood"]["annual_frequency"]
    lm = doc["loss_magnitude"]
    return AtlasScenario(
        id=doc["id"],
        title=doc["title"],
        version=doc["version"],
        sector=doc["sector"],
        soci_asset_class=doc["soci_asset_class"],
        summary=doc["summary"],
        mitre_tactics=doc["mitre_attack"]["tactics"],
        mitre_techniques=doc["mitre_attack"]["techniques"],
        nodes=nodes,
        edges=edges,
        annual_frequency=BetaPert(
            min=lik["min"], mode=lik["mode"], max=lik["max"], notes=lik.get("notes")
        ),
        primary_response=BetaPert(**lm["primary_response"]),
        secondary_response=BetaPert(**lm["secondary_response"]),
        currency=lm.get("currency", "AUD"),
        references=list(doc["references"]),
        controls_suggested=list(doc.get("controls_suggested", [])),
        last_reviewed=doc.get("last_reviewed", ""),
    )

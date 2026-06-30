# SOCI Threat Atlas — Scenario Schema

This document is the human-readable companion to [`schema/scenario.schema.json`](schema/scenario.schema.json). The JSON Schema is authoritative; this document explains intent.

## File conventions

- One scenario per file.
- Path: `scenarios/<sector>/<ID>-<kebab-case-slug>.yaml`
- Filename ID must match the `id:` field inside the file.
- All scenarios MUST be public-release (TLP:CLEAR or TLP:GREEN). Restricted content is rejected at PR review.

## Required top-level fields

| Field | Type | Notes |
|---|---|---|
| `id` | string | `WAT-001`, `ELE-014`, etc. Sector prefix + 3 digits. Once issued, never reused. |
| `title` | string | Plain English. Used in citations. |
| `version` | string | SemVer. Bump on every merged change. |
| `sector` | enum | `water`, `electricity`, `gas`, `ports`, `aviation`, `healthcare` |
| `soci_asset_class` | string | Asset class under the SOCI Act 2018 schedule. |
| `classification` | enum | `TLP:CLEAR` or `TLP:GREEN`. |
| `summary` | string | 80–1200 chars. The first paragraph displayed in the browser. |
| `mitre_attack` | object | At least one tactic and one technique. |
| `nodes` | array | At least 2. See below. |
| `edges` | array | At least 1. See below. |
| `likelihood` | object | Beta-PERT triple (min/mode/max annual frequency) + rationale. |
| `loss_magnitude` | object | Beta-PERT triples for primary and secondary response (AUD). |
| `references` | array | Public sources only. URLs, CISA/ACSC advisories, OAIC NDB reports, academic papers. |
| `maintainers` | array | GitHub handles. |
| `last_reviewed` | date | `YYYY-MM-DD`. Scenarios not reviewed in 18 months fail CI. |
| `license` | const | `MIT`. |

## Sector prefixes

| Prefix | Sector |
|---|---|
| `WAT` | water |
| `ELE` | electricity |
| `GAS` | gas |
| `POR` | ports |
| `AVI` | aviation |
| `HLT` | healthcare |

## Nodes

Each node represents an asset, person, or external actor on the attack path. Required fields:

- `id` — kebab-case, unique within the scenario
- `type` — `it_asset` | `ot_asset` | `iot_asset` | `vendor_asset` | `external` | `person` | `data_store`
- `description` — what this is in plain English
- `scannable` — boolean. If `false`, `reason_unscannable` is required.
- `criticality` — `low` | `medium` | `high` | `critical`

The `scannable: false` flag is deliberate. It is the signal that distinguishes a SOCI Threat Atlas scenario from a generic IT threat model. SOCI assets are the ones automated scanners cannot reach. Flag this honestly.

Valid `reason_unscannable` values:

- `safety_critical_air_gapped`
- `vendor_support_prohibits_agents`
- `legacy_unsupported_os`
- `embedded_constrained_device`
- `third_party_no_access`
- `classified_policy_prohibits`
- `operational_disruption_risk`

## Edges

Each edge is an attack step from one node to another. Required:

- `from`, `to` — node IDs (use `external` for internet-origin steps)
- `technique` — MITRE ATT&CK technique ID
- `detection_difficulty` — `very_low` | `low` | `medium` | `high` | `very_high`
- `notes` — optional but recommended; cite the public source that grounds this step

## Beta-PERT triples

`min`, `mode`, `max` define a Beta-PERT distribution. Be conservative:

- `min` = the lowest credible value for this scenario at this organisation type
- `mode` = the most likely value
- `max` = the worst credible value (not the absolute worst case)

For `likelihood.annual_frequency`, values are events per year. `0.04` means a 4% annual chance.

For `loss_magnitude`, values are AUD by default. Override with `currency: USD` if a source is USD-denominated.

## What does NOT belong in a scenario file

- Calibration data (Brier scores, market prices)
- Cross-scenario propagation weights
- Posterior updates from real engagements
- Customer-specific asset names, IPs, or hostnames
- Any TLP:AMBER or higher content
- Speculation framed as fact — every step needs a public reference

## Validating locally

```bash
pip install jsonschema pyyaml
python tools/validate.py
```

Exit code 0 = clean; non-zero = at least one failure printed to stderr.

## Versioning

When you change a scenario:

- **Patch** (`1.0.0` → `1.0.1`): typo, reference correction, controls list edit
- **Minor** (`1.0.0` → `1.1.0`): new edge added, prior refined with new evidence
- **Major** (`1.0.0` → `2.0.0`): scenario re-modelled (different nodes, different attack path)

The scenario `id` never changes. If you want a fundamentally different scenario, file a new one.

# SOCI Threat Atlas

**Open-source threat graphs for Australian critical infrastructure.**
MIT-licensed. Maintained by [CyQuantiFi](https://cyquantifi.com).

> *"Put a dollar figure on every cyber risk — even the ones you can't scan."*

[![Validate](https://github.com/cyquantifi/soci-threat-graphs/actions/workflows/validate.yml/badge.svg)](https://github.com/cyquantifi/soci-threat-graphs/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-FF8818.svg)](LICENSE)
[![Browse online](https://img.shields.io/badge/Browse-cyquantifi.github.io-EA7A10.svg)](https://cyquantifi.github.io/soci-threat-graphs/)

---

## What this is

A growing library of **machine-readable threat scenarios** for assets regulated under the Australian Security of Critical Infrastructure Act 2018 (SOCI). Each scenario is a graph fragment — nodes, edges, MITRE ATT&CK mapping, Beta-PERT priors, and public-source references — designed to be dropped straight into a quantitative cyber risk model.

The atlas exists because **no public, structured, machine-readable threat library covers Australian critical infrastructure**. Every CISO writing a CIRMP, every consultancy delivering a SOCI engagement, and every regulator drafting guidance currently starts from a blank page or a generic global catalogue. The atlas is that blank page filled in, with attribution, under MIT.

## Who this is for

- **CISOs and risk leads** at SOCI-regulated entities (water, electricity, gas, ports, aviation, healthcare) preparing or refreshing a CIRMP
- **Consultancies and IRAP assessors** delivering SOCI engagements who want defensible priors rather than gut-feel ranges
- **Regulators and policy teams** seeking a common reference set
- **Researchers** studying critical-infrastructure cyber risk

## Format

One scenario per YAML file. Sector prefix + 3-digit ID (`WAT-001`, `ELE-014`). Each scenario is self-contained and references only public sources.

See [`SCHEMA.md`](SCHEMA.md) for the human-readable spec and [`schema/scenario.schema.json`](schema/scenario.schema.json) for the JSON Schema (CI-enforced).

Example scenario:

```yaml
id: WAT-001
title: SCADA compromise via engineering workstation pivot
sector: water
soci_asset_class: water_and_sewerage
classification: TLP:CLEAR
mitre_attack:
  tactics: [TA0001, TA0008, TA0040]
  techniques:
    - id: T1190
      name: Exploit Public-Facing Application
nodes:
  - id: scada_hmi
    type: ot_asset
    scannable: false
    reason_unscannable: vendor_support_prohibits_agents
    criticality: high
edges:
  - from: engineering_workstation
    to: scada_hmi
    technique: T1078
    detection_difficulty: high
likelihood:
  annual_frequency: { min: 0.005, mode: 0.04, max: 0.20 }
loss_magnitude:
  primary_response: { min: 250000, mode: 1200000, max: 5000000 }
  secondary_response: { min: 500000, mode: 8000000, max: 80000000 }
references:
  - "CISA advisory AA21-287A"
  - "ACSC Annual Cyber Threat Report 2024-25"
```

## Sectors covered

| Sector | Asset class | Status |
|---|---|---|
| Water | Water and sewerage | Seed (1 scenario) |
| Electricity | Electricity | Seed (1 scenario) |
| Gas | Gas | Planned |
| Ports | Ports | Seed (1 scenario) |
| Aviation | Aviation | Seed (1 scenario) |
| Healthcare | Health care and medical | Seed (1 scenario) |

Target: ~50 scenarios at general availability. See [milestones](https://github.com/cyquantifi/soci-threat-graphs/milestones).

## The unscannable-asset wedge

Each scenario explicitly flags assets as `scannable: true` or `scannable: false`. The `false` cases — OT/SCADA, air-gapped systems, vendor-managed devices, legacy unsupported OS, embedded IoT, third-party systems — are where existing IT-centric threat catalogues fall down. They are also where SOCI obligations are most material.

We require contributors to be honest about scannability. It is the most important signal in a SOCI scenario.

## Using the atlas

### As a human

Browse the static site at [cyquantifi.github.io/soci-threat-graphs](https://cyquantifi.github.io/soci-threat-graphs/). Each scenario page lists the attack graph, MITRE mapping, priors, suggested controls, and references. Copy the YAML into your own tooling, or cite the scenario ID in your CIRMP.

### As a machine

```bash
git clone https://github.com/cyquantifi/soci-threat-graphs.git
pip install pyyaml jsonschema
python tools/validate.py
```

Scenarios are valid YAML and conform to the JSON Schema in `schema/`. Parse and ingest them with whatever tooling you use.

### With CyQuantiFi

The atlas is the open-source prior. [CyQuantiFi](https://cyquantifi.com) is the platform that runs the math — Monte Carlo simulation against your asset inventory, calibrated expert input via prediction markets, ALE in dollars, board-ready reports.

Each scenario page on the atlas links to a deep-import URL: `app.cyquantifi.com/import?scenario=WAT-001` pre-populates the CyQuantiFi graph editor with the atlas scenario. From there you adjust nodes for your environment, layer in your own evidence, and run.

See [docs/using-with-cyquantifi.md](docs/using-with-cyquantifi.md) for the full integration.

## Citation

If you use the atlas in a CIRMP, board paper, research output, or commercial engagement, please cite it. See [`CITATION.cff`](CITATION.cff). Quotable form:

> SOCI Threat Atlas v1.0. CyQuantiFi Pty Ltd, 2026. https://github.com/cyquantifi/soci-threat-graphs

## Contributing

PRs welcome from operators, consultancies, regulators, and researchers. See [`CONTRIBUTING.md`](CONTRIBUTING.md). All scenarios must be public-release (TLP:CLEAR/GREEN) and reference public sources.

## License

[MIT](LICENSE). Free for commercial use with attribution.

## Maintainers

[CyQuantiFi Pty Ltd](https://cyquantifi.com) — ABN 67 697 329 105

Open an issue for corrections, new scenario proposals, or schema feedback.

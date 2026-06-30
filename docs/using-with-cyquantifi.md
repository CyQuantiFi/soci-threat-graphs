# Using the SOCI Threat Atlas with CyQuantiFi

The atlas is the open layer. [CyQuantiFi](https://cyquantifi.com) is the math layer. They are designed to compose.

## What the atlas gives you

- A defensible **prior** for likelihood and loss magnitude, grounded in public evidence
- A structured **graph fragment** — nodes, edges, MITRE mapping — ready for a quantitative risk model
- A common **citation** ("per WAT-001 in the SOCI Threat Atlas...") your board, your regulator, and your assurance partner can recognise

## What the atlas does not give you

- A probability calibrated to **your** operator's specific environment
- A **posterior** that updates as new evidence arrives
- **Monte Carlo** output in dollars
- A **board paper** or CIRMP-ready report

These are CyQuantiFi's job.

## Three ways to use the two together

### 1. Browser deep-link

On any scenario page, click **Run this scenario in CyQuantiFi**. The deep link `app.cyquantifi.com/import?scenario=WAT-001` opens the CyQuantiFi graph editor with the atlas scenario pre-loaded. From there you adjust nodes for your environment, layer in your evidence, and run Monte Carlo.

### 2. CLI

```bash
cyquantifi atlas list --sector water
cyquantifi atlas import WAT-001 --project-id <uuid>
cyquantifi atlas import-all --sector electricity --project-id <uuid>
```

The CLI pulls scenarios directly from the GitHub raw URL, validates against the schema, and creates a graph in the target project.

### 3. API

```http
POST /api/v1/scenarios/import
Content-Type: application/json
Authorization: Bearer <token>

{
  "atlas_id": "WAT-001",
  "project_id": "...",
  "ref": "v1.0.0"
}
```

Pin to a specific atlas version with `ref` if you want stable imports across re-runs.

## What CyQuantiFi adds on top

| Layer | Atlas | CyQuantiFi |
|---|---|---|
| Graph structure | ✓ | ✓ (imported) |
| MITRE mapping | ✓ | ✓ (imported) |
| Public-evidence prior | ✓ | ✓ (imported) |
| Monte Carlo simulation | | ✓ |
| Calibrated expert input | | ✓ |
| Cross-tenant data flywheel | | ✓ |
| ALE in dollars | | ✓ |
| Board-ready report | | ✓ |
| Continuous re-run on schedule | | ✓ |

## Why the atlas stays open

A vendor-controlled threat library is worth less than a community-controlled one — CISOs and regulators discount marketing-coloured content. By keeping the atlas MIT-licensed, vendor-neutral on its surface, and accepting external maintainers, the atlas becomes a citable industry artefact. CyQuantiFi competes on the math layer, not on access to the priors.

# Contributing to the SOCI Threat Atlas

Thanks for considering a contribution. The atlas only works if it is honest, current, and grounded in evidence. The bar is high but the process is simple.

## Three rules

1. **Public sources only.** Every claim in a scenario must trace to a public reference — CISA / ACSC advisory, OAIC NDB report, regulator publication, academic paper, mainstream press coverage of a disclosed incident, or vendor public threat report. No internal incidents, no client engagements, no speculation framed as fact.
2. **TLP:CLEAR or TLP:GREEN only.** Restricted content is rejected. If you need to model a sensitive scenario, do it in your own environment — the atlas is the public layer.
3. **Be honest about scannability.** The `scannable: false` flag is the most important signal in a SOCI scenario. Do not over-state what scanners can reach.

## What kinds of contributions are accepted

- **New scenarios** for sectors and asset classes covered by SOCI
- **Corrections** to existing scenarios — references, priors, MITRE mapping, controls
- **Schema improvements** — new fields, tighter validation, better enums
- **Tooling** — better validators, renderers, exporters (STIX, OpenC2, etc.)
- **Translations** — once the English library is stable

## What is not accepted

- Scenarios based on confidential client engagements
- Calibration data (Brier scores, market prices, posterior updates) — these belong in the consuming platform, not the open library
- Vendor-product-specific exploit detail beyond what is publicly disclosed
- Scenarios that exist only in theory with no public corroboration

## How to add a new scenario

1. Open an issue using the **New scenario** template with the proposed ID and a one-paragraph rationale. A maintainer will confirm the ID is unused and the scenario is in scope.
2. Fork the repo and create a branch.
3. Add your scenario file under `scenarios/<sector>/<ID>-<kebab-case-slug>.yaml`.
4. Run `python tools/validate.py` locally. CI will run it on your PR.
5. Open a PR. Use the **New scenario** PR template.
6. A maintainer reviews for evidence quality, structural validity, and overlap with existing scenarios. Substantive feedback within 14 days.

## How to correct an existing scenario

- Open an issue using the **Correction** template, or jump straight to a PR if the change is small (typo, broken URL, controls update).
- Bump the `version` field per the SemVer policy in [`SCHEMA.md`](SCHEMA.md).
- Update `last_reviewed` to today's date.

## Style

- Plain English. No marketing voice.
- Specific over general. "Engineering workstation" not "endpoint".
- Cite the specific advisory or report, not just the organisation.
- Use AUD unless the source is in another currency.

## Conduct

Be useful to the people who will use this library to defend critical infrastructure. That is the whole point.

## Licence on contributions

By contributing you agree your contribution is licensed under the MIT licence of this repository.

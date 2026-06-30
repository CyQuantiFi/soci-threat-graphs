#!/usr/bin/env python3
"""
Render every scenario YAML to a static HTML page under docs/scenarios/
and write an index page under docs/index.html.

The HTML deliberately uses no external CSS so the file is self-contained
and renders even when served from raw GitHub. GitHub Pages can wrap it in
a theme if desired.

Usage:
    python tools/render.py
"""
from __future__ import annotations

import html
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.stderr.write("Missing dependency: pip install pyyaml\n")
    sys.exit(3)

REPO_ROOT = Path(__file__).resolve().parent.parent
SCENARIOS_DIR = REPO_ROOT / "scenarios"
OUTPUT_DIR = REPO_ROOT / "docs" / "scenarios"
INDEX_PATH = REPO_ROOT / "docs" / "index.html"

CYQUANTIFI_DEEPLINK = "https://app.cyquantifi.com/import?scenario={id}"

PAGE_CSS = """
  body { font-family: 'Segoe UI', system-ui, sans-serif; max-width: 860px; margin: 2em auto;
         padding: 0 1em; color: #1f2937; background: #fafafa; }
  h1 { color: #1f2937; border-bottom: 3px solid #FF8818; padding-bottom: .3em; }
  h2 { color: #EA7A10; margin-top: 1.5em; }
  .meta { color: #6b7280; font-size: .9em; }
  .chip { display: inline-block; padding: 2px 10px; margin: 2px;
          background: #fff7ed; color: #EA7A10; border: 1px solid #fed7aa;
          border-radius: 12px; font-size: .85em; }
  .chip.unscannable { background: #fff1f2; color: #be123c; border-color: #fecdd3; }
  .cta { background: #fff; border: 2px solid #FF8818; border-radius: 8px;
         padding: 1.2em; margin: 2em 0; }
  .cta a { background: #FF8818; color: white; padding: .6em 1.2em;
           text-decoration: none; border-radius: 6px; font-weight: 600;
           display: inline-block; margin-top: .6em; }
  table { border-collapse: collapse; width: 100%; margin: 1em 0; }
  th, td { text-align: left; padding: .5em; border-bottom: 1px solid #e5e7eb; }
  th { background: #f3f4f6; }
  code { background: #f3f4f6; padding: 1px 6px; border-radius: 3px;
         font-family: 'SFMono-Regular', Consolas, monospace; font-size: .9em; }
  pre { background: #f3f4f6; padding: 1em; border-radius: 6px; overflow-x: auto; }
  .footer { color: #9ca3af; font-size: .85em; margin-top: 3em;
            border-top: 1px solid #e5e7eb; padding-top: 1em; }
"""


def esc(value) -> str:
    return html.escape(str(value), quote=True)


def render_chips(items, css="chip"):
    return " ".join(f'<span class="{css}">{esc(i)}</span>' for i in items)


def render_scenario(doc: dict) -> str:
    sid = doc["id"]
    title = doc["title"]
    tactics = doc["mitre_attack"]["tactics"]
    techniques = doc["mitre_attack"]["techniques"]

    node_rows = []
    for node in doc["nodes"]:
        scannable_label = (
            f'<span class="chip">scannable</span>'
            if node["scannable"]
            else f'<span class="chip unscannable">unscannable: '
                 f'{esc(node.get("reason_unscannable", "unspecified"))}</span>'
        )
        node_rows.append(
            f"<tr><td><code>{esc(node['id'])}</code></td>"
            f"<td>{esc(node['type'])}</td>"
            f"<td>{esc(node['description'])}</td>"
            f"<td>{esc(node['criticality'])}</td>"
            f"<td>{scannable_label}</td></tr>"
        )

    edge_rows = []
    for edge in doc["edges"]:
        edge_rows.append(
            f"<tr><td><code>{esc(edge['from'])}</code> → <code>{esc(edge['to'])}</code></td>"
            f"<td><code>{esc(edge['technique'])}</code></td>"
            f"<td>{esc(edge['detection_difficulty'])}</td>"
            f"<td>{esc(edge.get('notes', ''))}</td></tr>"
        )

    lik = doc["likelihood"]["annual_frequency"]
    prim = doc["loss_magnitude"]["primary_response"]
    sec = doc["loss_magnitude"]["secondary_response"]
    currency = doc["loss_magnitude"].get("currency", "AUD")

    refs = "\n".join(f"<li>{esc(r)}</li>" for r in doc["references"])

    deep_link = CYQUANTIFI_DEEPLINK.format(id=sid)

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>{esc(sid)} — {esc(title)} | SOCI Threat Atlas</title>
<meta name="description" content="{esc(doc['summary'][:160])}">
<style>{PAGE_CSS}</style>
</head><body>
<p class="meta"><a href="../index.html">&larr; SOCI Threat Atlas</a> · Sector: {esc(doc['sector'])} ·
  Asset class: {esc(doc['soci_asset_class'])} · {esc(doc['classification'])}</p>
<h1>{esc(sid)} · {esc(title)}</h1>
<p>{esc(doc['summary'])}</p>

<h2>MITRE ATT&amp;CK mapping</h2>
<p><strong>Tactics:</strong> {render_chips(tactics)}</p>
<p><strong>Techniques:</strong> {render_chips(f"{t['id']} {t['name']}" for t in techniques)}</p>

<h2>Nodes</h2>
<table><thead><tr><th>ID</th><th>Type</th><th>Description</th><th>Criticality</th><th>Scannable?</th></tr></thead>
<tbody>{"".join(node_rows)}</tbody></table>

<h2>Edges</h2>
<table><thead><tr><th>From → To</th><th>Technique</th><th>Detection</th><th>Notes</th></tr></thead>
<tbody>{"".join(edge_rows)}</tbody></table>

<h2>Priors (Beta-PERT)</h2>
<p><strong>Annual frequency:</strong> min {lik['min']} · mode {lik['mode']} · max {lik['max']}</p>
<p class="meta">{esc(doc['likelihood']['rationale'])}</p>
<p><strong>Primary response ({currency}):</strong>
   ${prim['min']:,} / ${prim['mode']:,} / ${prim['max']:,}</p>
<p><strong>Secondary response ({currency}):</strong>
   ${sec['min']:,} / ${sec['mode']:,} / ${sec['max']:,}</p>

<div class="cta">
  <strong>Want a calibrated probability for your operator?</strong>
  <p class="meta">The atlas gives you a defensible prior. CyQuantiFi runs Monte Carlo against
  your own asset inventory, refines the prior with calibrated expert input, and outputs ALE
  in dollars — ready for a CIRMP or board paper.</p>
  <a href="{deep_link}">Run {esc(sid)} in CyQuantiFi &rarr;</a>
</div>

<h2>Suggested controls</h2>
<ul>
{"".join(f"<li><code>{esc(c['id'])}</code> — {esc(c['name'])} <span class='meta'>({esc(c.get('framework', ''))})</span></li>" for c in doc.get('controls_suggested', []))}
</ul>

<h2>References</h2>
<ul>{refs}</ul>

<p class="footer">
  Version {esc(doc['version'])} · Last reviewed {esc(doc['last_reviewed'])} ·
  Maintainers: {esc(', '.join(doc['maintainers']))} ·
  MIT-licensed · Maintained by <a href="https://cyquantifi.com">CyQuantiFi Pty Ltd</a>
</p>
</body></html>
"""


def render_index(scenarios: list[dict]) -> str:
    by_sector: dict[str, list[dict]] = {}
    for s in scenarios:
        by_sector.setdefault(s["sector"], []).append(s)

    sections = []
    for sector in sorted(by_sector):
        items = sorted(by_sector[sector], key=lambda s: s["id"])
        rows = "".join(
            f'<li><a href="scenarios/{s["id"]}.html"><code>{esc(s["id"])}</code> — {esc(s["title"])}</a></li>'
            for s in items
        )
        sections.append(f"<h2>{esc(sector.capitalize())}</h2><ul>{rows}</ul>")

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>SOCI Threat Atlas — Open-source threat graphs for AU critical infrastructure</title>
<meta name="description" content="Open-source threat graphs for Australian critical infrastructure. MIT-licensed.">
<style>{PAGE_CSS}</style>
</head><body>
<h1>SOCI Threat Atlas</h1>
<p>Open-source threat graphs for Australian critical infrastructure.
   MIT-licensed. Maintained by <a href="https://cyquantifi.com">CyQuantiFi</a>.</p>
<p class="meta">{len(scenarios)} scenarios across {len(by_sector)} sectors.
   Format: machine-readable YAML with MITRE ATT&amp;CK mapping, Beta-PERT priors, and public references.
   Designed to be imported directly into a quantitative risk model.</p>

<div class="cta">
  <strong>Using the atlas in a CIRMP, board paper, or SOCI engagement?</strong>
  <p class="meta">The atlas provides defensible priors grounded in public evidence.
  CyQuantiFi runs the math layer — Monte Carlo simulation, calibrated expert input,
  ALE in dollars — and imports atlas scenarios directly.</p>
  <a href="https://cyquantifi.com">Learn how CyQuantiFi uses the atlas &rarr;</a>
</div>

{"".join(sections)}

<p class="footer">
  MIT-licensed · <a href="https://github.com/cyquantifi/soci-threat-graphs">GitHub</a> ·
  <a href="https://github.com/cyquantifi/soci-threat-graphs/blob/main/CONTRIBUTING.md">Contribute a scenario</a>
</p>
</body></html>
"""


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    scenarios: list[dict] = []
    for path in sorted(SCENARIOS_DIR.glob("**/*.yaml")):
        with path.open() as fh:
            doc = yaml.safe_load(fh)
        scenarios.append(doc)
        out = OUTPUT_DIR / f"{doc['id']}.html"
        out.write_text(render_scenario(doc))
        print(f"rendered {out.relative_to(REPO_ROOT)}")

    INDEX_PATH.write_text(render_index(scenarios))
    print(f"rendered {INDEX_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

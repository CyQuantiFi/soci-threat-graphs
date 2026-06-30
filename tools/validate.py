#!/usr/bin/env python3
"""
Validate every scenario YAML against schema/scenario.schema.json.

Usage:
    python tools/validate.py [--strict-review-age]

Exit codes:
    0  every scenario passed
    1  one or more scenarios failed schema validation
    2  one or more scenarios are stale (>18 months since last_reviewed)
       only enforced with --strict-review-age
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.stderr.write("Missing dependency: pip install pyyaml\n")
    sys.exit(3)

try:
    from jsonschema import Draft202012Validator
except ImportError:
    sys.stderr.write("Missing dependency: pip install jsonschema\n")
    sys.exit(3)


REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "schema" / "scenario.schema.json"
SCENARIO_GLOB = "scenarios/**/*.yaml"
STALE_THRESHOLD_DAYS = 18 * 30  # ~18 months


def load_schema() -> dict:
    with SCHEMA_PATH.open() as fh:
        return json.load(fh)


def iter_scenario_paths() -> list[Path]:
    return sorted(REPO_ROOT.glob(SCENARIO_GLOB))


def validate_scenario(path: Path, validator: Draft202012Validator) -> list[str]:
    errors: list[str] = []
    try:
        with path.open() as fh:
            doc = yaml.safe_load(fh)
    except yaml.YAMLError as exc:
        return [f"YAML parse error: {exc}"]

    if not isinstance(doc, dict):
        return ["Top-level YAML must be a mapping"]

    for err in sorted(validator.iter_errors(doc), key=lambda e: list(e.absolute_path)):
        loc = "/".join(str(p) for p in err.absolute_path) or "<root>"
        errors.append(f"{loc}: {err.message}")

    expected_dir = doc.get("sector")
    if expected_dir and expected_dir != path.parent.name:
        errors.append(
            f"Scenario sector '{expected_dir}' does not match parent directory '{path.parent.name}'"
        )

    fname_id = path.stem.split("-")[0:2]
    if len(fname_id) >= 2:
        fname_id_str = "-".join(fname_id)
        if doc.get("id") != fname_id_str:
            errors.append(
                f"Scenario id '{doc.get('id')}' does not match filename id '{fname_id_str}'"
            )

    seen_node_ids: set[str] = set()
    for node in doc.get("nodes", []) or []:
        nid = node.get("id")
        if nid in seen_node_ids:
            errors.append(f"Duplicate node id: {nid}")
        seen_node_ids.add(nid)

    for edge in doc.get("edges", []) or []:
        for end in ("from", "to"):
            ref = edge.get(end)
            if ref and ref != "external" and ref not in seen_node_ids:
                errors.append(f"Edge references unknown node '{ref}' (in {end})")

    return errors


def check_review_age(path: Path) -> str | None:
    try:
        with path.open() as fh:
            doc = yaml.safe_load(fh)
    except Exception:
        return None
    last = doc.get("last_reviewed")
    if not last:
        return None
    try:
        last_date = dt.date.fromisoformat(last)
    except ValueError:
        return f"Invalid last_reviewed date: {last}"
    age = (dt.date.today() - last_date).days
    if age > STALE_THRESHOLD_DAYS:
        return f"Scenario stale: last_reviewed {age} days ago (limit {STALE_THRESHOLD_DAYS})"
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict-review-age", action="store_true")
    args = parser.parse_args()

    schema = load_schema()
    validator = Draft202012Validator(schema)

    paths = iter_scenario_paths()
    if not paths:
        sys.stderr.write("No scenarios found under scenarios/**/*.yaml\n")
        return 1

    schema_failures = 0
    stale_failures = 0
    for path in paths:
        rel = path.relative_to(REPO_ROOT)
        errs = validate_scenario(path, validator)
        if errs:
            schema_failures += 1
            print(f"FAIL  {rel}")
            for e in errs:
                print(f"      - {e}")
            continue
        stale = check_review_age(path)
        if stale:
            stale_failures += 1
            tag = "STALE" if args.strict_review_age else "warn "
            print(f"{tag} {rel}  ({stale})")
            continue
        print(f"PASS  {rel}")

    print()
    print(f"Scenarios: {len(paths)}  Pass: {len(paths) - schema_failures - stale_failures}  "
          f"Schema fail: {schema_failures}  Stale: {stale_failures}")

    if schema_failures:
        return 1
    if args.strict_review_age and stale_failures:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

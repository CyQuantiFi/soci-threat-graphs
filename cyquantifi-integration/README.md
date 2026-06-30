# CyQuantiFi integration code

These files are stubs to drop into the main CyQuantiFi backend (`backend/src/...`).
They implement the import bridge described in the proposal: a parser, a service
that maps atlas YAML to CyQuantiFi internal models, and a FastAPI route.

These files do **not** belong in the public `soci-threat-graphs` repo — they
live here in the same workspace for convenience while developing. Move them
into `cyquantifi-demo/backend/` when ready.

## Target paths in the main repo

```
backend/src/parsers/atlas_yaml_parser.py
backend/src/services/soci_atlas_importer.py
backend/src/routes/scenario_import.py
backend/src/schemas/atlas_import.py
backend/tests/test_atlas_importer.py
```

## Wiring

In `backend/src/main.py`, register the router alongside the other routes:

```python
from src.routes import scenario_import
app.include_router(scenario_import.router)
```

## CLI

In the `cyquantifi-demo` repo's CLI module (or as a small standalone tool):

```
cyquantifi atlas list --sector water
cyquantifi atlas import WAT-001 --project-id <uuid>
cyquantifi atlas import-all --sector electricity --project-id <uuid>
```

The CLI can be a thin wrapper around the same parser plus an HTTP client to the route.

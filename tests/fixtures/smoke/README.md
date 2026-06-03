# Smoke fixture layout

Each curated catalog entry maps to a directory under `tests/fixtures/smoke/<fixture-id>/`:

- `source.pdf` — downloaded from `pdf_url` (gitignored)
- `reference.md` — optional reference markdown from `markdown_url` (gitignored)
- `output/` — persisted conversion artifacts from smoke runs (gitignored)

Materialize sources:

```powershell
uv run python scripts/fetch_fixtures.py --catalog tests/fixtures/fixture_catalog.curated.json
```

Run conversions and persist artifacts:

```powershell
uv run python scripts/run_smoke_fixtures.py --catalog tests/fixtures/fixture_catalog.curated.json
```

Integration smoke tests use the same layout when `PAPER_MARKER_FIXTURE_CATALOG` points at the curated catalog.

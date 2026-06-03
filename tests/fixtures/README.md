# Fixture Sourcing Notes

Testing and validation should include diverse document sources, with examples gathered from:

- Marker documentation/tests and sample PDFs
- MinerU documentation/tests and sample PDFs
- Nougat documentation/tests and sample PDFs
- MarkItDown documentation/tests and sample PDFs

Target source categories for fixtures:
- born-digital scientific papers
- scanned papers
- textbook-style pages
- math-heavy documents
- table-heavy documents

Concrete upstream starting points:
- Marker: <https://github.com/datalab-to/marker>
- MinerU: <https://github.com/opendatalab/MinerU>
- Nougat: <https://github.com/facebookresearch/nougat>
- MarkItDown: <https://github.com/microsoft/markitdown>

Real fixture execution model:
- Use `tests/fixtures/fixture_catalog.example.json` as the template for a local fixture catalog.
- Copy it to a real catalog path and point `PAPER_MARKER_FIXTURE_CATALOG` to it.
- Integration tests will run real converter checks only when this catalog exists and route CLIs are available.

Curated web-sourced candidates:
- `tests/fixtures/fixture_catalog.curated.json` contains starter candidates from official library docs/tests first, then broader PDF+Markdown sources.
- Each entry uses the smoke layout documented in `tests/fixtures/smoke/README.md` (`source.pdf`, optional `reference.md`, persisted `output/`).
- To materialize local PDFs and reference markdown from that catalog:
  - `uv run python scripts/fetch_fixtures.py --catalog tests/fixtures/fixture_catalog.curated.json`
- To run conversions and persist artifacts under each fixture's `output/` directory:
  - `uv run python scripts/run_smoke_fixtures.py --catalog tests/fixtures/fixture_catalog.curated.json`
- Then run integration validation by pointing:
  - `PAPER_MARKER_FIXTURE_CATALOG=tests/fixtures/fixture_catalog.curated.json`

Catalog URL validation:
- Validate links before download:
  - `uv run python scripts/validate_fixture_catalog.py --catalog tests/fixtures/fixture_catalog.curated.json`
- Optionally write a report:
  - `uv run python scripts/validate_fixture_catalog.py --catalog tests/fixtures/fixture_catalog.curated.json --output tests/fixtures/fixture_catalog_validation.json`

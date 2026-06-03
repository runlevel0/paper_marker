from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from paper_marker.fixtures.catalog import (
    catalog_entry_paths,
    load_catalog,
    run_smoke_entry,
    smoke_output_dir,
)

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG = WORKSPACE_ROOT / "tests/fixtures/fixture_catalog.curated.json"


def _load_smoke_catalog() -> list[dict]:
    catalog_path = os.getenv("PAPER_MARKER_FIXTURE_CATALOG")
    path = Path(catalog_path) if catalog_path else DEFAULT_CATALOG
    if not path.exists():
        pytest.skip(f"Fixture catalog does not exist: {path}")
    return load_catalog(path)


@pytest.mark.integration
def test_smoke_fixture_persists_output_artifacts() -> None:
    catalog = _load_smoke_catalog()
    executed = 0
    for entry in catalog:
        pdf_path, _ = catalog_entry_paths(entry, WORKSPACE_ROOT)
        if not pdf_path.exists():
            continue
        try:
            run_smoke_entry(entry, WORKSPACE_ROOT)
        except (FileNotFoundError, RuntimeError):
            continue

        out_dir = smoke_output_dir(entry, WORKSPACE_ROOT)
        assert (out_dir / "final.md").exists(), f"Missing final.md for {entry['id']}"
        assert (out_dir / "run_report.json").exists(), f"Missing run_report.json for {entry['id']}"
        assert (out_dir / "final_result.json").exists(), (
            f"Missing final_result.json for {entry['id']}"
        )
        report = json.loads((out_dir / "run_report.json").read_text(encoding="utf-8"))
        assert report["selected_route"] == entry["route"]
        executed += 1
        break

    if executed == 0:
        pytest.skip("No smoke fixtures executed (missing PDFs and/or route CLIs).")

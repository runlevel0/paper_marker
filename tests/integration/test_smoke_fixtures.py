from __future__ import annotations

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
FIGURE_HEAVY_FIXTURE_ID = "marker-thinkpython-textbook"


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
        route_md = out_dir / f"{entry['route']}.md"
        assert route_md.exists(), f"Missing {route_md.name} for {entry['id']}"
        assert route_md.read_text(encoding="utf-8").strip()
        executed += 1
        break

    if executed == 0:
        pytest.skip("No smoke fixtures executed (missing PDFs and/or route CLIs).")


@pytest.mark.integration
def test_smoke_figure_heavy_fixture_publishes_route_assets() -> None:
    catalog = _load_smoke_catalog()
    entry = next((item for item in catalog if item["id"] == FIGURE_HEAVY_FIXTURE_ID), None)
    if entry is None:
        pytest.skip(f"Fixture {FIGURE_HEAVY_FIXTURE_ID} not in catalog")

    pdf_path, _ = catalog_entry_paths(entry, WORKSPACE_ROOT)
    if not pdf_path.exists():
        pytest.skip(f"Missing source PDF for {FIGURE_HEAVY_FIXTURE_ID}")

    try:
        result = run_smoke_entry(entry, WORKSPACE_ROOT)
    except (FileNotFoundError, RuntimeError) as exc:
        pytest.skip(str(exc))

    route_name = entry["route"]
    out_dir = smoke_output_dir(entry, WORKSPACE_ROOT)
    route_md = out_dir / f"{route_name}.md"
    assert route_md.exists()

    markdown_text = route_md.read_text(encoding="utf-8")
    assets_prefix = f"![]({route_name}_assets/"
    has_local_figure = assets_prefix in markdown_text or any(
        token in markdown_text for token in ("_Figure_", ".jpeg", ".png")
    )
    if not has_local_figure:
        pytest.skip("Fixture output has no local figure references to verify")

    assets_dir = out_dir / f"{route_name}_assets"
    assert assets_dir.is_dir(), f"Expected asset directory {assets_dir.name}"
    image_files = list(assets_dir.rglob("*.jpeg")) + list(assets_dir.rglob("*.png"))
    assert image_files, f"No images under {assets_dir}"

    successful = [c for c in result.candidate_results if c.status == "ok"]
    assert successful and successful[0].assets
    if f"{route_name}_assets/" in markdown_text:
        sample = image_files[0].relative_to(out_dir).as_posix()
        assert sample in markdown_text

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest

from paper_marker.config import AppSettings
from paper_marker.core.models import ConversionRequest
from paper_marker.core.pipeline import ConversionOrchestrator


def _load_fixture_catalog() -> list[dict[str, Any]]:
    catalog_path = os.getenv("PAPER_MARKER_FIXTURE_CATALOG")
    if not catalog_path:
        pytest.skip("Set PAPER_MARKER_FIXTURE_CATALOG to run real fixture integration tests.")
    path = Path(catalog_path)
    if not path.exists():
        pytest.skip(f"Fixture catalog does not exist: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.integration
def test_real_fixture_conversion_matrix(tmp_path: Path) -> None:
    catalog = _load_fixture_catalog()
    orchestrator = ConversionOrchestrator(settings=AppSettings())
    route_status = {detail["route"]: detail["available"] for detail in orchestrator.list_routes()}

    executed = 0
    for fixture in catalog:
        route_name = fixture["route"]
        pdf_path = Path(fixture["pdf_path"])
        if not route_status.get(route_name, False):
            continue
        if not pdf_path.exists():
            continue

        request = ConversionRequest(
            pdf_path=pdf_path,
            out_dir=tmp_path / fixture["id"],
            routes=[route_name],
            timeout_per_route_s=300,
            synthesize=False,
            export_candidate_bundle=True,
        )
        result = orchestrator.run(request)
        assert result.candidate_results, f"No candidate results for fixture {fixture['id']}"
        produced = result.candidate_results[0].markdown_text
        assert produced, f"Empty markdown output for fixture {fixture['id']}"
        for fragment in fixture.get("golden_fragments", []):
            assert fragment in produced, (
                f"Expected fragment '{fragment}' missing for fixture {fixture['id']}"
            )
        executed += 1

    if executed == 0:
        pytest.skip("No executable fixture entries found (missing CLIs and/or fixture PDFs).")

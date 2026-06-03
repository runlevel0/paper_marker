from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from paper_marker.routes import DEFAULT_ROUTES

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"
REQUIRED_ENTRY_KEYS = ("id", "category", "route", "pdf_path", "golden_fragments", "source")


def _load_catalog(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def _routes_in_catalog(catalog: list[dict[str, Any]]) -> set[str]:
    return {entry["route"] for entry in catalog}


@pytest.mark.parametrize(
    "catalog_name",
    ["fixture_catalog.example.json", "fixture_catalog.curated.json"],
)
def test_fixture_catalog_entries_have_required_fields(catalog_name: str) -> None:
    catalog = _load_catalog(FIXTURES_DIR / catalog_name)
    assert catalog, f"{catalog_name} must contain at least one entry"
    for entry in catalog:
        for key in REQUIRED_ENTRY_KEYS:
            assert key in entry, f"{catalog_name} entry {entry.get('id')} missing '{key}'"
        assert entry["route"] in DEFAULT_ROUTES
        assert isinstance(entry["golden_fragments"], list)
        assert entry["golden_fragments"], (
            f"{catalog_name} entry {entry['id']} must declare golden_fragments"
        )
        assert str(entry["source"]).startswith("http"), (
            f"{catalog_name} entry {entry['id']} must document provenance URL in source"
        )


def test_fixture_catalog_example_covers_all_default_routes() -> None:
    catalog = _load_catalog(FIXTURES_DIR / "fixture_catalog.example.json")
    assert _routes_in_catalog(catalog) == set(DEFAULT_ROUTES)


def test_fixture_catalog_curated_covers_all_default_routes() -> None:
    catalog = _load_catalog(FIXTURES_DIR / "fixture_catalog.curated.json")
    assert set(DEFAULT_ROUTES).issubset(_routes_in_catalog(catalog))


def test_fixture_catalog_curated_documents_license_notes() -> None:
    catalog = _load_catalog(FIXTURES_DIR / "fixture_catalog.curated.json")
    for entry in catalog:
        assert entry.get("license_notes"), (
            f"Curated entry {entry['id']} must include license_notes for provenance"
        )


def test_fixture_catalog_curated_entries_with_urls_have_pdf_url() -> None:
    catalog = _load_catalog(FIXTURES_DIR / "fixture_catalog.curated.json")
    for entry in catalog:
        if entry.get("markdown_url") is not None:
            assert entry.get("pdf_url"), (
                f"Curated entry {entry['id']} with markdown_url should include pdf_url"
            )


def test_fixture_catalog_curated_uses_smoke_layout_paths() -> None:
    catalog = _load_catalog(FIXTURES_DIR / "fixture_catalog.curated.json")
    for entry in catalog:
        assert entry["pdf_path"].startswith("tests/fixtures/smoke/")
        assert entry["pdf_path"].endswith("/source.pdf")
        if entry.get("markdown_url"):
            markdown_path = entry.get("markdown_path")
            assert markdown_path, (
                f"Curated entry {entry['id']} with markdown_url must declare markdown_path"
            )
            assert markdown_path.startswith("tests/fixtures/smoke/")
            assert markdown_path.endswith("/reference.md")

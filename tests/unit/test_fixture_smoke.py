from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

from paper_marker.fixtures.catalog import (
    catalog_entry_paths,
    materialize_catalog,
    smoke_output_dir,
)

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]


def test_catalog_entry_paths_resolves_markdown_optional() -> None:
    entry: dict[str, Any] = {
        "id": "demo",
        "pdf_path": "tests/fixtures/smoke/demo/source.pdf",
        "markdown_path": "tests/fixtures/smoke/demo/reference.md",
    }
    pdf_path, markdown_path = catalog_entry_paths(entry, WORKSPACE_ROOT)
    assert pdf_path == WORKSPACE_ROOT / "tests/fixtures/smoke/demo/source.pdf"
    assert markdown_path == WORKSPACE_ROOT / "tests/fixtures/smoke/demo/reference.md"


def test_smoke_output_dir_under_fixture_id() -> None:
    entry = {"id": "marker-demo"}
    out_dir = smoke_output_dir(entry, WORKSPACE_ROOT)
    assert out_dir == WORKSPACE_ROOT / "tests/fixtures/smoke/marker-demo/output"


def test_materialize_catalog_downloads_pdf_and_markdown(tmp_path: Path) -> None:
    catalog = [
        {
            "id": "demo",
            "pdf_url": "https://example.com/source.pdf",
            "markdown_url": "https://example.com/reference.md",
            "pdf_path": "tests/fixtures/smoke/demo/source.pdf",
            "markdown_path": "tests/fixtures/smoke/demo/reference.md",
        }
    ]
    pdf_target = tmp_path / "tests/fixtures/smoke/demo/source.pdf"
    md_target = tmp_path / "tests/fixtures/smoke/demo/reference.md"

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.content = b"fixture-bytes"

    with patch("paper_marker.fixtures.catalog.httpx.Client") as client_cls:
        client = client_cls.return_value.__enter__.return_value
        client.get.return_value = mock_response
        stats = materialize_catalog(catalog, tmp_path, overwrite=False)

    assert stats["downloaded_pdfs"] == 1
    assert stats["downloaded_markdowns"] == 1
    assert pdf_target.read_bytes() == b"fixture-bytes"
    assert md_target.read_bytes() == b"fixture-bytes"
    assert client.get.call_count == 2


def test_materialize_catalog_skips_existing_without_overwrite(tmp_path: Path) -> None:
    catalog = [
        {
            "id": "demo",
            "pdf_url": "https://example.com/source.pdf",
            "pdf_path": "tests/fixtures/smoke/demo/source.pdf",
        }
    ]
    pdf_target = tmp_path / "tests/fixtures/smoke/demo/source.pdf"
    pdf_target.parent.mkdir(parents=True, exist_ok=True)
    pdf_target.write_bytes(b"existing")

    with patch("paper_marker.fixtures.catalog.httpx.Client") as client_cls:
        stats = materialize_catalog(catalog, tmp_path, overwrite=False)

    assert stats["downloaded_pdfs"] == 0
    assert stats["skipped"] == 1
    client_cls.return_value.__enter__.return_value.get.assert_not_called()

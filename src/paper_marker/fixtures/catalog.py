from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx

from paper_marker.config import AppSettings
from paper_marker.core.models import ConversionRequest, FinalResult
from paper_marker.core.pipeline import ConversionOrchestrator

SMOKE_ROOT = Path("tests/fixtures/smoke")


def load_catalog(path: Path) -> list[dict[str, Any]]:
    data: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        msg = f"Fixture catalog must be a JSON array: {path}"
        raise ValueError(msg)
    return data


def catalog_entry_paths(entry: dict[str, Any], workspace_root: Path) -> tuple[Path, Path | None]:
    pdf_path = workspace_root / entry["pdf_path"]
    markdown_path_raw = entry.get("markdown_path")
    markdown_path = workspace_root / markdown_path_raw if markdown_path_raw else None
    return pdf_path, markdown_path


def smoke_output_dir(entry: dict[str, Any], workspace_root: Path) -> Path:
    entry_id = entry["id"]
    if not isinstance(entry_id, str):
        msg = "Fixture catalog entry id must be a string"
        raise ValueError(msg)
    return workspace_root / SMOKE_ROOT / entry_id / "output"


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def download_file(url: str, path: Path, timeout_s: float = 120.0) -> None:
    _ensure_parent(path)
    with httpx.Client(timeout=timeout_s, follow_redirects=True) as client:
        response = client.get(url)
        response.raise_for_status()
        path.write_bytes(response.content)


def materialize_catalog(
    catalog: list[dict[str, Any]],
    workspace_root: Path,
    *,
    overwrite: bool,
    timeout_s: float = 120.0,
) -> dict[str, int]:
    downloaded_pdfs = 0
    downloaded_markdowns = 0
    skipped = 0
    for entry in catalog:
        pdf_url = entry.get("pdf_url")
        pdf_path, markdown_path = catalog_entry_paths(entry, workspace_root)
        if pdf_url:
            if pdf_path.exists() and not overwrite:
                skipped += 1
            else:
                download_file(pdf_url, pdf_path, timeout_s=timeout_s)
                downloaded_pdfs += 1
        else:
            skipped += 1

        markdown_url = entry.get("markdown_url")
        if markdown_url and markdown_path is not None:
            if markdown_path.exists() and not overwrite:
                skipped += 1
            else:
                download_file(markdown_url, markdown_path, timeout_s=timeout_s)
                downloaded_markdowns += 1
    return {
        "downloaded_pdfs": downloaded_pdfs,
        "downloaded_markdowns": downloaded_markdowns,
        "skipped": skipped,
    }


def run_smoke_entry(
    entry: dict[str, Any],
    workspace_root: Path,
    *,
    settings: AppSettings | None = None,
    timeout_per_route_s: int = 300,
) -> FinalResult:
    pdf_path, _ = catalog_entry_paths(entry, workspace_root)
    if not pdf_path.exists():
        msg = f"Missing source PDF for fixture {entry['id']}: {pdf_path}"
        raise FileNotFoundError(msg)

    orchestrator = ConversionOrchestrator(settings=settings or AppSettings())
    route_name = entry["route"]
    route_status = {detail["route"]: detail["available"] for detail in orchestrator.list_routes()}
    if not route_status.get(route_name, False):
        msg = f"Route '{route_name}' CLI is not available for fixture {entry['id']}"
        raise RuntimeError(msg)

    out_dir = smoke_output_dir(entry, workspace_root)
    request = ConversionRequest(
        pdf_path=pdf_path,
        out_dir=out_dir,
        routes=[route_name],
        timeout_per_route_s=timeout_per_route_s,
        synthesize=False,
    )
    result = orchestrator.run(request)
    produced = ""
    for candidate in result.candidate_results:
        if candidate.status == "ok" and candidate.markdown_text:
            produced = candidate.markdown_text
            break
    if not produced:
        msg = f"No successful markdown output for fixture {entry['id']}"
        raise RuntimeError(msg)
    for fragment in entry.get("golden_fragments", []):
        if fragment not in produced:
            msg = f"Expected fragment '{fragment}' missing for fixture {entry['id']}"
            raise AssertionError(msg)
    return result

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import httpx


def load_catalog(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def download_file(url: str, path: Path) -> None:
    ensure_parent(path)
    with httpx.Client(timeout=120.0, follow_redirects=True) as client:
        response = client.get(url)
        response.raise_for_status()
        path.write_bytes(response.content)


def materialize_catalog(
    catalog: list[dict[str, Any]], workspace_root: Path, overwrite: bool
) -> tuple[int, int]:
    downloaded = 0
    skipped = 0
    for entry in catalog:
        pdf_url = entry.get("pdf_url")
        pdf_path = entry.get("pdf_path")
        if not pdf_url or not pdf_path:
            skipped += 1
            continue
        target = workspace_root / pdf_path
        if target.exists() and not overwrite:
            skipped += 1
            continue
        download_file(pdf_url, target)
        downloaded += 1
    return downloaded, skipped


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download fixture PDFs from a curated fixture catalog."
    )
    parser.add_argument(
        "--catalog",
        default="tests/fixtures/fixture_catalog.curated.json",
        help="Path to fixture catalog JSON.",
    )
    parser.add_argument(
        "--workspace-root",
        default=".",
        help="Workspace root used to resolve pdf_path fields.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing local fixture files.",
    )
    args = parser.parse_args()

    workspace_root = Path(args.workspace_root).resolve()
    catalog_path = (workspace_root / args.catalog).resolve()
    catalog = load_catalog(catalog_path)
    downloaded, skipped = materialize_catalog(catalog, workspace_root, args.overwrite)
    print(
        json.dumps(
            {
                "catalog": str(catalog_path),
                "downloaded": downloaded,
                "skipped": skipped,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

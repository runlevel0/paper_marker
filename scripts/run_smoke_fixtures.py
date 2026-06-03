from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from paper_marker.fixtures.catalog import load_catalog, run_smoke_entry


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run curated PDF smoke conversions with persisted output artifacts."
    )
    parser.add_argument(
        "--catalog",
        default="tests/fixtures/fixture_catalog.curated.json",
        help="Path to fixture catalog JSON.",
    )
    parser.add_argument(
        "--workspace-root",
        default=".",
        help="Workspace root used to resolve catalog paths.",
    )
    parser.add_argument(
        "--fixture-id",
        default=None,
        help="Run a single fixture id instead of the full catalog.",
    )
    args = parser.parse_args()

    workspace_root = Path(args.workspace_root).resolve()
    catalog_path = (workspace_root / args.catalog).resolve()
    catalog = load_catalog(catalog_path)
    if args.fixture_id:
        catalog = [entry for entry in catalog if entry["id"] == args.fixture_id]
        if not catalog:
            raise SystemExit(f"Fixture id not found in catalog: {args.fixture_id}")

    results: list[dict[str, Any]] = []
    failures: list[str] = []
    for entry in catalog:
        fixture_id = entry["id"]
        try:
            final = run_smoke_entry(entry, workspace_root)
            results.append(
                {
                    "fixture_id": fixture_id,
                    "status": "ok",
                    "output_dir": final.output_dir,
                    "selected_route": final.selected_route,
                }
            )
        except FileNotFoundError as exc:
            results.append({"fixture_id": fixture_id, "status": "skipped", "reason": str(exc)})
        except RuntimeError as exc:
            reason = str(exc)
            results.append({"fixture_id": fixture_id, "status": "skipped", "reason": reason})
        except AssertionError as exc:
            failures.append(f"{fixture_id}: {exc}")
            results.append({"fixture_id": fixture_id, "status": "failed", "reason": str(exc)})

    summary = {
        "catalog": str(catalog_path),
        "attempted": len(catalog),
        "ok": sum(1 for row in results if row["status"] == "ok"),
        "skipped": sum(1 for row in results if row["status"] == "skipped"),
        "failed": len(failures),
        "results": results,
    }
    print(json.dumps(summary, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

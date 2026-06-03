from __future__ import annotations

import argparse
import json
from pathlib import Path

from paper_marker.fixtures.catalog import load_catalog, materialize_catalog


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download fixture PDFs and reference markdown from a curated catalog."
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
        "--overwrite",
        action="store_true",
        help="Overwrite existing local fixture files.",
    )
    args = parser.parse_args()

    workspace_root = Path(args.workspace_root).resolve()
    catalog_path = (workspace_root / args.catalog).resolve()
    catalog = load_catalog(catalog_path)
    stats = materialize_catalog(catalog, workspace_root, overwrite=args.overwrite)
    print(
        json.dumps(
            {
                "catalog": str(catalog_path),
                **stats,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

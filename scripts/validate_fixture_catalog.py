from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import httpx

PDF_MIME_HINTS = (
    "application/pdf",
    "application/x-pdf",
    "binary/octet-stream",
    "application/octet-stream",
)
MARKDOWN_MIME_HINTS = ("text/markdown", "text/plain", "text/x-markdown")


def load_catalog(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def _kind_from_field(field_name: str) -> str:
    return "pdf" if field_name == "pdf_url" else "markdown"


def _expected_mime(kind: str) -> tuple[str, ...]:
    if kind == "pdf":
        return PDF_MIME_HINTS
    return MARKDOWN_MIME_HINTS


def check_url(client: httpx.Client, url: str, kind: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "url": url,
        "kind": kind,
        "ok": False,
        "status_code": None,
        "content_type": None,
        "final_url": None,
        "error": None,
    }
    try:
        response = client.get(url, follow_redirects=True)
        content_type = (response.headers.get("content-type") or "").lower()
        expected_hints = _expected_mime(kind)
        mime_ok = any(hint in content_type for hint in expected_hints)
        status_ok = response.status_code == 200
        result.update(
            {
                "status_code": response.status_code,
                "content_type": content_type,
                "final_url": str(response.url),
                "ok": status_ok and mime_ok,
                "error": None
                if status_ok and mime_ok
                else f"Unexpected status/content-type ({response.status_code}, {content_type})",
            }
        )
    except Exception as exc:  # noqa: BLE001
        result["error"] = str(exc)
    return result


def validate_catalog(catalog: list[dict[str, Any]], timeout_s: float) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    with httpx.Client(timeout=timeout_s) as client:
        for entry in catalog:
            for field in ("pdf_url", "markdown_url"):
                url = entry.get(field)
                if not url:
                    continue
                kind = _kind_from_field(field)
                check = check_url(client, url, kind)
                check["fixture_id"] = entry.get("id")
                checks.append(check)

    failed = [check for check in checks if not check["ok"]]
    return {
        "total_checks": len(checks),
        "passed": len(checks) - len(failed),
        "failed": len(failed),
        "failures": failed,
        "checks": checks,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate pdf_url/markdown_url links in a fixture catalog."
    )
    parser.add_argument(
        "--catalog",
        default="tests/fixtures/fixture_catalog.curated.json",
        help="Path to fixture catalog JSON.",
    )
    parser.add_argument(
        "--workspace-root",
        default=".",
        help="Workspace root used to resolve catalog path.",
    )
    parser.add_argument(
        "--timeout-s",
        type=float,
        default=30.0,
        help="HTTP timeout in seconds per request.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional path to write JSON report.",
    )
    args = parser.parse_args()

    workspace_root = Path(args.workspace_root).resolve()
    catalog_path = (workspace_root / args.catalog).resolve()
    catalog = load_catalog(catalog_path)
    report = validate_catalog(catalog, timeout_s=args.timeout_s)
    report["catalog"] = str(catalog_path)

    if args.output:
        output_path = (workspace_root / args.output).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(report, indent=2))
    if report["failed"] > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

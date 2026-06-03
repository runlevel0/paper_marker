from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx

REPO = "runlevel0/paper_marker"
API_BASE = "https://api.github.com"
DEFAULT_LEDGER = Path("docs/implementation_issues.md")
DEFAULT_LABELS = Path(".github/labels.yml")
DEFAULT_MAP = Path("docs/archive/github_issue_map.json")

SECTION_KEYS = ("Evidence", "Fix Plan", "Verification", "Done Criteria")


@dataclass
class IssueEntry:
    legacy_id: str
    number: int
    title: str
    severity: str
    status: str
    areas: list[str]
    evidence: str
    fix_plan: str
    verification: str
    done_criteria: str
    related: list[str] = field(default_factory=list)

    @property
    def is_done(self) -> bool:
        return self.status.lower() == "done"

    def labels(self) -> list[str]:
        labels = [
            f"severity/{self.severity.lower()}",
            "legacy-ledger",
            *[f"area/{area}" for area in self.areas],
        ]
        return labels

    def github_title(self) -> str:
        return f"[{self.legacy_id}] {self.title}"

    def github_body(self) -> str:
        related = ""
        if self.related:
            related = "\n## Related\n" + "\n".join(f"- {item}" for item in self.related) + "\n"
        return (
            f"**Legacy ID:** {self.legacy_id}\n"
            f"**Severity:** {self.severity}\n"
            f"**Status:** {self.status}\n\n"
            f"## Evidence\n{self.evidence.strip()}\n\n"
            f"## Fix Plan\n{self.fix_plan.strip()}\n\n"
            f"## Verification\n{self.verification.strip()}\n\n"
            f"## Done Criteria\n{self.done_criteria.strip()}\n"
            f"{related}"
        )


ISSUE_META: dict[int, dict[str, Any]] = {
    1: {"title": "Fixture-backed real converter integration", "areas": ["testing"]},
    2: {"title": "Add keep-temp flag to CLI", "areas": ["cli"]},
    3: {"title": "Validate route names before worker dispatch", "areas": ["pipeline"]},
    4: {"title": "Synthesis prompt budget controls", "areas": ["pipeline"]},
    5: {"title": "Dataclass vs Pydantic modeling policy", "areas": ["docs"]},
    6: {"title": "LICENSE and PyPI package metadata", "areas": ["packaging"]},
    7: {"title": "CI and publish workflows on main", "areas": ["packaging"]},
    8: {"title": "Stop tracking egg-info build artifacts", "areas": ["packaging"]},
    9: {
        "title": "Route-attributed worker failures and all-routes-failed state",
        "areas": ["pipeline"],
    },
    10: {"title": "Route and synthesis HTTP unit test coverage", "areas": ["testing"]},
    11: {"title": "Static type checker in CI", "areas": ["testing"]},
    12: {"title": "CONTRIBUTING, CHANGELOG, and .env.example", "areas": ["docs"]},
    13: {"title": "Structured logging across pipeline and routes", "areas": ["pipeline"]},
    14: {"title": "Shared CLI-route helper refactor", "areas": ["pipeline"]},
    15: {"title": "Synthesis HTTP retry with backoff", "areas": ["pipeline"]},
    16: {"title": "Rename resources folder to canonical spelling", "areas": ["docs"]},
    17: {
        "title": "CLI, MCP, and README documentation completeness",
        "areas": ["docs", "cli", "mcp"],
    },
    18: {"title": "Installation docs and install smoke CI", "areas": ["docs", "packaging"]},
    19: {"title": "PDF smoke tests with persisted artifacts", "areas": ["testing"]},
    20: {"title": "Mandatory output directory for convert", "areas": ["cli", "mcp"]},
    21: {"title": "Lean flat output layout (one markdown per route)", "areas": ["pipeline"]},
    22: {"title": "Asset copy and path rewriting for route figures", "areas": ["pipeline"]},
}


LOST_ISSUES: dict[int, dict[str, str]] = {
    17: {
        "severity": "Medium",
        "status": "open",
        "evidence": (
            "- CLI (`src/paper_marker/cli.py`): only the root Typer app has a one-line `help=` string. "
            "Commands `list-routes`, `doctor`, and `convert` have no docstrings. All `convert` options "
            "omit Typer `help=` text, so `--help` surfaces bare parameter names with no usage guidance.\n"
            "- MCP (`src/paper_marker/mcp/server.py`): tool functions have no docstrings or parameter "
            "descriptions. Contract tests assert `description` is a string but not that it is meaningful.\n"
            "- README omits `doctor`, `--routes`, `--timeout-per-route`, valid route names, run outputs, "
            "MCP parameters, and sample MCP client configuration."
        ),
        "fix_plan": (
            "- Add command docstrings and per-option `help=` strings to `cli.py`.\n"
            "- Add tool and parameter docstrings in `mcp/server.py` mirroring CLI semantics.\n"
            "- Expand README with doctor, route selection, outputs, synthesis prerequisites, and MCP setup.\n"
            "- Tighten MCP contract tests for non-empty descriptions."
        ),
        "verification": (
            "- `paper-marker --help` and subcommand helps show descriptive text for every command and option.\n"
            "- MCP `tools/list` shows non-empty descriptions for all three tools.\n"
            '- `uv run pytest -m "not integration"` remains green.'
        ),
        "done_criteria": (
            "- CLI and MCP self-document at the interface boundary.\n"
            "- README covers all user-facing commands, flags, outputs, and MCP setup."
        ),
    },
    18: {
        "severity": "Medium",
        "status": "open",
        "evidence": (
            "- README has a short dev-focused install block; end-user PyPI install lives only in `docs/release.md`.\n"
            "- CI uses `uv sync` (editable workspace), not install-from-wheel.\n"
            "- Publish workflow builds artifacts but never installs them or validates console scripts.\n"
            "- MCP smoke check runs via `uv run paper-marker-mcp`, not installed entry points."
        ),
        "fix_plan": (
            "- Add dedicated Installation section (README and/or `docs/installation.md`).\n"
            "- Add install smoke test: build wheel, clean install, assert `paper-marker --help`, "
            "`list-routes`, MCP `tools/list`.\n"
            "- Wire install verification into CI (PR job or publish quality gate)."
        ),
        "verification": (
            "- Manual: follow install doc on clean venv; both entry points work.\n"
            "- CI install-smoke job passes on PRs."
        ),
        "done_criteria": (
            "- End users can install and verify without reading source.\n"
            "- CI fails if console scripts or package metadata prevent install-and-run smoke."
        ),
    },
    19: {
        "severity": "High",
        "status": "open",
        "evidence": (
            "- `scripts/fetch_fixtures.py` downloads PDFs only; `markdown_url` entries are ignored.\n"
            "- Integration tests write outputs to pytest `tmp_path` (discarded after run).\n"
            "- Assertions use short `golden_fragments` only.\n"
            "- Real fixture tests are opt-in and excluded from default CI."
        ),
        "fix_plan": (
            "- Extend catalog with `markdown_path`; update fetcher to download reference markdown.\n"
            "- Define `tests/fixtures/smoke/<fixture-id>/` layout with source, reference, and `output/`.\n"
            "- Add smoke test module and `scripts/run_smoke_fixtures.py`.\n"
            "- CI nightly/workflow: download fixtures, run smoke, upload artifacts."
        ),
        "verification": (
            "- Fetch materializes PDFs and reference markdowns.\n"
            "- Smoke run persists co-located artifacts.\n"
            "- CI smoke job uploads artifact bundle."
        ),
        "done_criteria": (
            "- Every curated catalog entry can be downloaded, converted, and inspected on disk.\n"
            "- CI runs smoke suite and preserves artifacts for review."
        ),
    },
    20: {
        "severity": "Medium",
        "status": "open",
        "evidence": (
            '- CLI: `convert` treats `--out-dir` as optional with default `Path("out")`.\n'
            '- MCP: `convert_pdf_to_markdown` declares `out_dir: str = "out"`.\n'
            "- Users can convert without choosing an output location explicitly."
        ),
        "fix_plan": (
            "- Make `--out-dir` required on CLI (no default).\n"
            "- Remove MCP default for `out_dir`; require in tool schema.\n"
            "- Update tests, README, CHANGELOG (breaking change)."
        ),
        "verification": (
            "- `paper-marker convert paper.pdf` without `--out-dir` fails with clear message.\n"
            "- MCP call without `out_dir` fails validation.\n"
            "- Explicit `--out-dir` path still succeeds."
        ),
        "done_criteria": (
            "- Neither CLI nor MCP accepts convert without explicit output directory."
        ),
    },
    21: {
        "severity": "Medium",
        "status": "open",
        "evidence": (
            "- Pipeline writes `candidate_bundle/`, `final.md`, `run_report.json`, `final_result.json`.\n"
            "- CLI/MCP JSON stdout duplicates on-disk JSON files.\n"
            "- `--export-candidate-bundle` only toggles bundle subtree."
        ),
        "fix_plan": (
            "- Write flat `{route}.md` in `out_dir`; optional `synthesized.md` when `--synthesize`.\n"
            "- Keep structured metadata in CLI/MCP JSON response only.\n"
            "- Remove or repurpose `export_candidate_bundle`.\n"
            "- Document failure = no markdown file; defer assets to ISSUE-022."
        ),
        "verification": (
            "- Two-route convert yields only `{route}.md` files (+ `synthesized.md` if requested).\n"
            "- No `candidate_bundle/`, `run_report.json`, or `final_result.json` by default.\n"
            "- JSON responses still include candidate statuses and selection metadata."
        ),
        "done_criteria": (
            "- Default disk output is flat: one markdown per successful route, optional synthesized.md.\n"
            "- Edge cases documented and tested."
        ),
        "related": ["Follow-up for figures: ISSUE-022"],
    },
    22: {
        "severity": "Medium",
        "status": "open",
        "evidence": (
            "- Routes (Marker, MinerU) write figures under `_work/`; pipeline copies markdown text only.\n"
            "- `CandidateResult.assets` is never populated.\n"
            "- Lean `{route}.md` in `out_dir` breaks relative image links without `--keep-temp`."
        ),
        "fix_plan": (
            "- Discover non-markdown outputs after each route run; populate `CandidateResult.assets`.\n"
            "- Copy assets to `out_dir` (e.g. `{route}_assets/`).\n"
            "- Rewrite relative image/link paths in `{route}.md`.\n"
            "- Add unit tests with synthetic `_work/` trees; figure-heavy smoke fixture."
        ),
        "verification": (
            "- Figure-heavy PDF: `out_dir/marker.md` renders images without `--keep-temp`.\n"
            "- JSON response lists copied asset paths."
        ),
        "done_criteria": (
            "- Portable `{route}.md` renders figures correctly for asset-emitting routes.\n"
            "- Asset layout documented; ISSUE-021 lean layout preserved."
        ),
        "related": ["Depends on / follows ISSUE-021 lean output layout"],
    },
}


def _extract_section(block: str, section: str) -> str:
    pattern = rf"- {re.escape(section)}:\n(.*?)(?=\n- [A-Z]|\Z)"
    match = re.search(pattern, block, flags=re.DOTALL)
    if not match:
        return ""
    lines = match.group(1).splitlines()
    cleaned: list[str] = []
    for line in lines:
        if line.startswith("  "):
            cleaned.append(line[2:])
        elif line.strip() == "":
            cleaned.append("")
    return "\n".join(cleaned).strip()


def _parse_field(block: str, field_name: str) -> str:
    match = re.search(rf"- {field_name}: (.+)", block)
    return match.group(1).strip() if match else ""


def parse_ledger(path: Path) -> dict[int, dict[str, str]]:
    text = path.read_text(encoding="utf-8")
    entries: dict[int, dict[str, str]] = {}
    for match in re.finditer(r"## (ISSUE-\d+)\n(.*?)(?=\n## ISSUE-|\Z)", text, flags=re.DOTALL):
        legacy_id = match.group(1)
        block = match.group(2)
        number = int(legacy_id.split("-")[1])
        entries[number] = {
            "legacy_id": legacy_id,
            "severity": _parse_field(block, "Severity"),
            "status": _parse_field(block, "Status"),
            "evidence": _extract_section(block, "Evidence"),
            "fix_plan": _extract_section(block, "Fix Plan"),
            "verification": _extract_section(block, "Verification"),
            "done_criteria": _extract_section(block, "Done Criteria"),
        }
    return entries


def build_issue_entries(ledger_path: Path) -> list[IssueEntry]:
    parsed = parse_ledger(ledger_path)
    for number, payload in LOST_ISSUES.items():
        parsed[number] = {
            "legacy_id": f"ISSUE-{number:03d}",
            **payload,
        }
    issues: list[IssueEntry] = []
    for number in sorted(parsed):
        raw = parsed[number]
        meta = ISSUE_META[number]
        related = raw.get("related", [])
        if isinstance(related, str):
            related = [related]
        issues.append(
            IssueEntry(
                legacy_id=raw["legacy_id"],
                number=number,
                title=meta["title"],
                severity=raw["severity"],
                status=raw["status"],
                areas=meta["areas"],
                evidence=raw["evidence"],
                fix_plan=raw["fix_plan"],
                verification=raw["verification"],
                done_criteria=raw["done_criteria"],
                related=list(related),
            )
        )
    return issues


def _token_from_git_credential() -> str | None:
    result = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    password: str | None = None
    for line in result.stdout.splitlines():
        if line.startswith("password="):
            password = line.removeprefix("password=").strip()
    return password or None


def resolve_token(explicit: str | None) -> str:
    if explicit:
        return explicit
    for key in ("GH_TOKEN", "GITHUB_TOKEN"):
        value = os.environ.get(key)
        if value:
            return value
    gh = shutil.which("gh")
    if gh:
        result = subprocess.run(
            [gh, "auth", "token"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    git_token = _token_from_git_credential()
    if git_token:
        return git_token
    raise SystemExit(
        "GitHub token required. Set GH_TOKEN or GITHUB_TOKEN, or authenticate `gh auth login`."
    )


class GitHubClient:
    def __init__(self, token: str, repo: str = REPO) -> None:
        self.repo = repo
        self.client = httpx.Client(
            base_url=API_BASE,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=60.0,
        )

    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> GitHubClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        response = self.client.request(method, path, **kwargs)
        if response.status_code >= 400:
            raise RuntimeError(f"{method} {path} failed ({response.status_code}): {response.text}")
        return response

    def list_issues_by_search(self, legacy_id: str) -> list[dict[str, Any]]:
        query = f'repo:{self.repo} "{legacy_id}" in:title'
        response = self._request(
            "GET",
            "/search/issues",
            params={"q": query, "per_page": 5},
        )
        return response.json().get("items", [])

    def create_label(self, name: str, color: str, description: str) -> None:
        response = self.client.post(
            f"/repos/{self.repo}/labels",
            json={"name": name, "color": color.lstrip("#"), "description": description},
        )
        if response.status_code == 422 and "already exists" in response.text:
            return
        if response.status_code >= 400:
            raise RuntimeError(f"create label {name} failed: {response.text}")

    def create_issue(self, entry: IssueEntry) -> int:
        response = self._request(
            "POST",
            f"/repos/{self.repo}/issues",
            json={
                "title": entry.github_title(),
                "body": entry.github_body(),
                "labels": entry.labels(),
            },
        )
        return int(response.json()["number"])

    def close_issue(self, issue_number: int, comment: str) -> None:
        self._request(
            "POST",
            f"/repos/{self.repo}/issues/{issue_number}/comments",
            json={"body": comment},
        )
        self._request(
            "PATCH",
            f"/repos/{self.repo}/issues/{issue_number}",
            json={"state": "closed", "state_reason": "completed"},
        )


def load_labels(labels_path: Path) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for raw_line in labels_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("- name:"):
            if current:
                items.append(current)
            current = {"name": line.split(":", 1)[1].strip()}
        elif line.startswith("color:"):
            current["color"] = line.split(":", 1)[1].strip()
        elif line.startswith("description:"):
            current["description"] = line.split(":", 1)[1].strip()
    if current:
        items.append(current)
    return items


def create_labels(client: GitHubClient, labels_path: Path) -> None:
    for label in load_labels(labels_path):
        client.create_label(label["name"], label["color"], label.get("description", ""))


def migrate(
    *,
    ledger_path: Path,
    labels_path: Path,
    map_path: Path,
    token: str | None,
    dry_run: bool,
    create_labels_only: bool,
) -> dict[str, int]:
    entries = build_issue_entries(ledger_path)
    if dry_run:
        for entry in entries:
            state = "close" if entry.is_done else "open"
            print(f"[dry-run] {entry.github_title()} -> {state} labels={entry.labels()}")
        return {}

    auth_token = resolve_token(token)
    mapping: dict[str, int] = {}
    if map_path.exists():
        mapping = json.loads(map_path.read_text(encoding="utf-8"))

    with GitHubClient(auth_token) as client:
        create_labels(client, labels_path)
        if create_labels_only:
            print("Labels created/verified.")
            return mapping

        for entry in entries:
            if entry.legacy_id in mapping:
                print(f"Skip {entry.legacy_id} (already mapped to #{mapping[entry.legacy_id]})")
                continue
            existing = client.list_issues_by_search(entry.legacy_id)
            if existing:
                issue_number = int(existing[0]["number"])
                print(f"Reuse {entry.legacy_id} -> #{issue_number} (found via search)")
            else:
                issue_number = client.create_issue(entry)
                print(f"Created {entry.legacy_id} -> #{issue_number}")
            mapping[entry.legacy_id] = issue_number
            if entry.is_done:
                client.close_issue(
                    issue_number,
                    "Migrated from markdown ledger (`docs/implementation_issues.md`); already complete.",
                )
                print(f"Closed #{issue_number}")

    map_path.parent.mkdir(parents=True, exist_ok=True)
    map_path.write_text(json.dumps(mapping, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return mapping


def write_recovered_archive(entries: list[IssueEntry], path: Path) -> None:
    lines = [
        "# Recovered ledger entries (ISSUE-017 through ISSUE-022)",
        "",
        "These entries were lost from `docs/implementation_issues.md` before GitHub Issues migration.",
        "",
    ]
    for entry in entries:
        if entry.number < 17:
            continue
        lines.extend(
            [
                f"## {entry.legacy_id}",
                f"- Severity: {entry.severity}",
                f"- Status: {entry.status}",
                "- Evidence:",
                *[f"  {line}" for line in entry.evidence.splitlines()],
                "- Fix Plan:",
                *[f"  {line}" for line in entry.fix_plan.splitlines()],
                "- Verification:",
                *[f"  {line}" for line in entry.verification.splitlines()],
                "- Done Criteria:",
                *[f"  {line}" for line in entry.done_criteria.splitlines()],
                "",
            ]
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate markdown issue ledger to GitHub Issues.")
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS)
    parser.add_argument("--map-file", type=Path, default=DEFAULT_MAP)
    parser.add_argument("--token", default=None, help="GitHub token (or GH_TOKEN / GITHUB_TOKEN).")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--create-labels-only", action="store_true")
    parser.add_argument(
        "--write-recovered-archive",
        type=Path,
        default=Path("docs/archive/implementation_issues_lost_entries_recovered.md"),
    )
    args = parser.parse_args()

    entries = build_issue_entries(args.ledger)
    write_recovered_archive(entries, args.write_recovered_archive)

    mapping = migrate(
        ledger_path=args.ledger,
        labels_path=args.labels,
        map_path=args.map_file,
        token=args.token,
        dry_run=args.dry_run,
        create_labels_only=args.create_labels_only,
    )
    print(json.dumps({"issues_migrated": len(mapping), "map_file": str(args.map_file)}, indent=2))


if __name__ == "__main__":
    main()

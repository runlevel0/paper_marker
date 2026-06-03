"""Discover route assets under _work/, copy to out_dir, and rewrite markdown paths."""

from __future__ import annotations

import re
import shutil
from pathlib import Path, PurePosixPath

from paper_marker.core.models import CandidateResult

_MARKDOWN_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
_MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[([^\]]*)\]\(([^)]+)\)")
_HTML_IMG_SRC_RE = re.compile(
    r"""<img\b[^>]*\bsrc=(["'])([^"']+)\1""",
    re.IGNORECASE,
)

_EXTERNAL_PREFIXES = (
    "http://",
    "https://",
    "//",
    "mailto:",
    "data:",
    "file:",
    "#",
)


def route_assets_dir_name(route_name: str) -> str:
    return f"{route_name}_assets"


def discover_route_asset_files(route_work_dir: Path) -> list[Path]:
    if not route_work_dir.is_dir():
        return []
    assets: list[Path] = []
    for path in sorted(route_work_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() == ".md":
            continue
        assets.append(path)
    return assets


def _is_external_reference(reference: str) -> bool:
    stripped = reference.strip()
    if not stripped:
        return True
    if stripped.startswith(_EXTERNAL_PREFIXES):
        return True
    if len(stripped) > 1 and stripped[1] == ":" and stripped[0].isalpha():
        return True
    return stripped.startswith(("/", "\\"))


def _normalize_reference(reference: str) -> str:
    cleaned = reference.strip().strip("<>").strip()
    if " " in cleaned and not cleaned.startswith(("'", '"')):
        cleaned = cleaned.split(" ", 1)[0]
    if cleaned.startswith(("'", '"')) and cleaned.endswith(("'", '"')) and len(cleaned) >= 2:
        cleaned = cleaned[1:-1]
    return PurePosixPath(cleaned.replace("\\", "/")).as_posix()


def _find_source_markdown(route_work_dir: Path, markdown_text: str) -> Path | None:
    for md_path in sorted(route_work_dir.rglob("*.md")):
        if md_path.read_text(encoding="utf-8", errors="ignore") == markdown_text:
            return md_path
    return None


def _lookup_published_path(
    reference: str,
    route_work_dir: Path,
    md_parent: Path,
    published_by_relative: dict[str, str],
) -> str | None:
    normalized = _normalize_reference(reference)
    if normalized in published_by_relative:
        return published_by_relative[normalized]
    search_bases = (md_parent, route_work_dir)
    for base in search_bases:
        candidate = (base / PurePosixPath(normalized)).resolve()
        try:
            relative = candidate.relative_to(route_work_dir.resolve()).as_posix()
        except ValueError:
            continue
        if relative in published_by_relative:
            return published_by_relative[relative]
    return None


def rewrite_markdown_asset_paths(
    markdown_text: str,
    *,
    route_work_dir: Path,
    published_by_relative: dict[str, str],
    md_parent: Path | None = None,
) -> str:
    if not published_by_relative:
        return markdown_text
    parent = md_parent if md_parent is not None else route_work_dir

    def _rewrite_reference(reference: str) -> str:
        if _is_external_reference(reference):
            return reference
        published = _lookup_published_path(
            reference,
            route_work_dir,
            parent,
            published_by_relative,
        )
        return published if published is not None else reference

    def _replace_markdown_image(match: re.Match[str]) -> str:
        alt, target = match.group(1), match.group(2)
        return f"![{alt}]({_rewrite_reference(target)})"

    def _replace_markdown_link(match: re.Match[str]) -> str:
        label, target = match.group(1), match.group(2)
        rewritten = _rewrite_reference(target)
        if rewritten == target:
            return match.group(0)
        return f"[{label}]({rewritten})"

    def _replace_html_img(match: re.Match[str]) -> str:
        quote, target = match.group(1), match.group(2)
        rewritten = _rewrite_reference(target)
        return match.group(0).replace(f"{quote}{target}{quote}", f"{quote}{rewritten}{quote}")

    updated = _MARKDOWN_IMAGE_RE.sub(_replace_markdown_image, markdown_text)
    updated = _MARKDOWN_LINK_RE.sub(_replace_markdown_link, updated)
    updated = _HTML_IMG_SRC_RE.sub(_replace_html_img, updated)
    return updated


def publish_route_assets(
    candidate: CandidateResult,
    route_work_dir: Path,
    out_dir: Path,
) -> CandidateResult:
    if candidate.status != "ok" or not candidate.markdown_text:
        return candidate

    asset_files = discover_route_asset_files(route_work_dir)
    if not asset_files:
        return candidate

    assets_root = out_dir / route_assets_dir_name(candidate.route_name)
    assets_root.mkdir(parents=True, exist_ok=True)

    published_by_relative: dict[str, str] = {}
    copied_paths: list[str] = []
    for source in asset_files:
        relative = source.relative_to(route_work_dir)
        destination = assets_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        relative_posix = relative.as_posix()
        published = f"{route_assets_dir_name(candidate.route_name)}/{relative_posix}"
        published_by_relative[relative_posix] = published
        copied_paths.append(str(destination.resolve()))

    source_md = _find_source_markdown(route_work_dir, candidate.markdown_text)
    md_parent = source_md.parent if source_md is not None else route_work_dir
    rewritten = rewrite_markdown_asset_paths(
        candidate.markdown_text,
        route_work_dir=route_work_dir,
        published_by_relative=published_by_relative,
        md_parent=md_parent,
    )
    return CandidateResult(
        route_name=candidate.route_name,
        status=candidate.status,
        markdown_text=rewritten,
        assets=copied_paths,
        error=candidate.error,
        elapsed_s=candidate.elapsed_s,
        metrics=candidate.metrics,
        metadata=candidate.metadata,
    )

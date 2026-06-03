from __future__ import annotations

from pathlib import Path

from paper_marker.core.assets import (
    discover_route_asset_files,
    publish_route_assets,
    rewrite_markdown_asset_paths,
    route_assets_dir_name,
)
from paper_marker.core.models import CandidateResult


def test_discover_route_asset_files_skips_markdown(tmp_path: Path) -> None:
    route_dir = tmp_path / "marker"
    route_dir.mkdir()
    (route_dir / "doc.md").write_text("# doc", encoding="utf-8")
    (route_dir / "fig.png").write_bytes(b"png")
    (route_dir / "nested").mkdir()
    (route_dir / "nested" / "chart.jpeg").write_bytes(b"jpeg")

    discovered = discover_route_asset_files(route_dir)

    assert [path.name for path in discovered] == ["fig.png", "chart.jpeg"]


def test_publish_route_assets_copies_and_rewrites(tmp_path: Path) -> None:
    route_dir = tmp_path / "work" / "marker"
    route_dir.mkdir(parents=True)
    image = route_dir / "_page_23_Figure_1.jpeg"
    image.write_bytes(b"jpeg")
    markdown = "Intro\n\n![](_page_23_Figure_1.jpeg)\n"
    (route_dir / "doc.md").write_text(markdown, encoding="utf-8")

    candidate = CandidateResult(route_name="marker", status="ok", markdown_text=markdown)
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    published = publish_route_assets(candidate, route_dir, out_dir)

    expected_asset = (out_dir / "marker_assets" / "_page_23_Figure_1.jpeg").resolve()
    assert published.assets == [str(expected_asset)]
    assert "![](marker_assets/_page_23_Figure_1.jpeg)" in published.markdown_text
    assert (out_dir / "marker_assets" / "_page_23_Figure_1.jpeg").exists()


def test_rewrite_markdown_leaves_external_urls_untouched(tmp_path: Path) -> None:
    route_dir = tmp_path / "marker"
    route_dir.mkdir()
    published = {"fig.png": "marker_assets/fig.png"}
    markdown = "![remote](https://example.com/x.png) ![local](fig.png)"

    rewritten = rewrite_markdown_asset_paths(
        markdown,
        route_work_dir=route_dir,
        published_by_relative=published,
    )

    assert "https://example.com/x.png" in rewritten
    assert "marker_assets/fig.png" in rewritten


def test_publish_route_assets_noop_without_assets(tmp_path: Path) -> None:
    route_dir = tmp_path / "marker"
    route_dir.mkdir()
    candidate = CandidateResult(route_name="marker", status="ok", markdown_text="# only text")

    published = publish_route_assets(candidate, route_dir, tmp_path / "out")

    assert published.assets == []
    assert published.markdown_text == "# only text"
    assert route_assets_dir_name("marker") == "marker_assets"

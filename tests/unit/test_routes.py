from __future__ import annotations

import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

from paper_marker.routes.base import ConversionRoute
from paper_marker.routes.marker_route import MarkerRoute
from paper_marker.routes.markitdown_route import MarkItDownRoute
from paper_marker.routes.mineru_route import MinerURoute
from paper_marker.routes.nougat_route import NougatRoute

ROUTE_CASES: list[tuple[type[ConversionRoute], str, str]] = [
    (MarkerRoute, "marker", "marker"),
    (MinerURoute, "mineru", "magic-pdf"),
    (NougatRoute, "nougat", "nougat"),
    (MarkItDownRoute, "markitdown", "markitdown"),
]


def _completed(
    returncode: int,
    stdout: str = "",
    stderr: str = "",
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=[],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


def _patch_resolve(
    monkeypatch: pytest.MonkeyPatch,
    route_module: str,
    resolver: Callable[[str], str | None],
) -> None:
    monkeypatch.setattr(f"paper_marker.routes.{route_module}.resolve_cli_executable", resolver)


def _route_module_name(route_cls: type[ConversionRoute]) -> str:
    return route_cls.__module__.rsplit(".", maxsplit=1)[-1]


def _resolve_cli(cli_name: str) -> Callable[[str], str | None]:
    def _resolver(command: str) -> str | None:
        if command == cli_name:
            return f"/bin/{command}"
        return None

    return _resolver


@pytest.mark.parametrize("route_cls, route_name, cli_name", ROUTE_CASES)
def test_route_is_available_when_cli_resolves(
    route_cls: type[ConversionRoute],
    route_name: str,
    cli_name: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del route_name
    module = _route_module_name(route_cls)
    _patch_resolve(monkeypatch, module, _resolve_cli(cli_name))
    route = route_cls()
    available, note = route.is_available()
    assert available is True
    assert cli_name in note


@pytest.mark.parametrize("route_cls, route_name, cli_name", ROUTE_CASES)
def test_route_is_unavailable_when_cli_missing(
    route_cls: type[ConversionRoute],
    route_name: str,
    cli_name: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del route_name, cli_name
    module = _route_module_name(route_cls)
    _patch_resolve(monkeypatch, module, lambda _command: None)
    route = route_cls()
    available, note = route.is_available()
    assert available is False
    assert "not found" in note


@pytest.mark.parametrize("route_cls, route_name, cli_name", ROUTE_CASES)
def test_convert_returns_unavailable_when_cli_missing(
    route_cls: type[ConversionRoute],
    route_name: str,
    cli_name: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    del cli_name
    module = _route_module_name(route_cls)
    _patch_resolve(monkeypatch, module, lambda _command: None)
    pdf_path = tmp_path / "paper.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")
    work_dir = tmp_path / "work"

    result = route_cls().convert(pdf_path, work_dir, timeout_s=30)

    assert result.route_name == route_name
    assert result.status == "unavailable"
    assert result.error is not None
    assert "not found" in result.error


@pytest.mark.parametrize("route_cls, route_name, cli_name", ROUTE_CASES)
def test_convert_success_reads_markdown_output(
    route_cls: type[ConversionRoute],
    route_name: str,
    cli_name: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _route_module_name(route_cls)
    _patch_resolve(monkeypatch, module, _resolve_cli(cli_name))

    def _run_success(
        cmd: list[str],
        capture_output: bool,
        text: bool,
        check: bool,
        timeout: int,
    ) -> subprocess.CompletedProcess[str]:
        del cmd, capture_output, text, check, timeout
        return _completed(0, stdout="# Title\n\nBody", stderr="")

    monkeypatch.setattr(f"paper_marker.routes.{module}.subprocess.run", _run_success)

    pdf_path = tmp_path / "paper.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")
    work_dir = tmp_path / "work"

    if route_name == "markitdown":
        expected_markdown = "# Title\n\nBody"
    else:
        out_dir = work_dir / route_name
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "output.md").write_text("# From file\n\n$x$", encoding="utf-8")
        expected_markdown = "# From file\n\n$x$"

    result = route_cls().convert(pdf_path, work_dir, timeout_s=30)

    assert result.status == "ok"
    assert result.markdown_text == expected_markdown
    assert result.error is None
    assert result.metrics is not None
    assert result.metadata["return_code"] == 0


@pytest.mark.parametrize("route_cls, route_name, cli_name", ROUTE_CASES)
def test_convert_error_when_cli_returns_nonzero(
    route_cls: type[ConversionRoute],
    route_name: str,
    cli_name: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    del route_name
    module = _route_module_name(route_cls)
    _patch_resolve(monkeypatch, module, _resolve_cli(cli_name))

    def _run_failure(
        cmd: list[str],
        capture_output: bool,
        text: bool,
        check: bool,
        timeout: int,
    ) -> subprocess.CompletedProcess[str]:
        del cmd, capture_output, text, check, timeout
        return _completed(1, stdout="", stderr="conversion failed")

    monkeypatch.setattr(f"paper_marker.routes.{module}.subprocess.run", _run_failure)

    pdf_path = tmp_path / "paper.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")
    work_dir = tmp_path / "work"

    result = route_cls().convert(pdf_path, work_dir, timeout_s=30)

    assert result.status == "error"
    assert result.markdown_text == ""
    assert result.error == "conversion failed"
    assert result.metadata["return_code"] == 1


@pytest.mark.parametrize("route_cls, route_name, cli_name", ROUTE_CASES)
def test_convert_timeout(
    route_cls: type[ConversionRoute],
    route_name: str,
    cli_name: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    del route_name
    module = _route_module_name(route_cls)
    _patch_resolve(monkeypatch, module, _resolve_cli(cli_name))

    def _run_timeout(
        cmd: list[str],
        capture_output: bool,
        text: bool,
        check: bool,
        timeout: int,
    ) -> subprocess.CompletedProcess[str]:
        del cmd, capture_output, text, check, timeout
        raise subprocess.TimeoutExpired(cmd=["fake"], timeout=30)

    monkeypatch.setattr(f"paper_marker.routes.{module}.subprocess.run", _run_timeout)

    pdf_path = tmp_path / "paper.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")
    work_dir = tmp_path / "work"

    result = route_cls().convert(pdf_path, work_dir, timeout_s=30)

    assert result.status == "timeout"
    assert "timed out" in (result.error or "")
    assert result.metadata["command"]

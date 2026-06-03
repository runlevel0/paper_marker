from __future__ import annotations

import sys
from pathlib import Path

import pytest

from paper_marker.routes.cli_discovery import resolve_cli_executable


def test_resolve_cli_executable_uses_path_first(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "paper_marker.routes.cli_discovery.shutil.which",
        lambda command: "/usr/bin/marker" if command == "marker" else None,
    )
    assert resolve_cli_executable("marker") == "/usr/bin/marker"


def test_resolve_cli_executable_falls_back_to_scripts_dir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr("paper_marker.routes.cli_discovery.shutil.which", lambda _command: None)
    monkeypatch.setattr(
        "paper_marker.routes.cli_discovery.sysconfig.get_path",
        lambda _name: str(tmp_path),
    )
    monkeypatch.setattr(
        "paper_marker.routes.cli_discovery._candidate_script_dirs",
        lambda: [tmp_path],
    )

    if sys.platform == "win32":
        (tmp_path / "marker.exe").write_text("", encoding="utf-8")
        expected = str(tmp_path / "marker.exe")
    else:
        marker = tmp_path / "marker"
        marker.write_text("", encoding="utf-8")
        marker.chmod(0o755)
        expected = str(marker)

    assert resolve_cli_executable("marker") == expected


def test_resolve_cli_executable_returns_none_when_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr("paper_marker.routes.cli_discovery.shutil.which", lambda _command: None)
    monkeypatch.setattr(
        "paper_marker.routes.cli_discovery._candidate_script_dirs",
        lambda: [tmp_path],
    )
    assert resolve_cli_executable("missing-cli") is None

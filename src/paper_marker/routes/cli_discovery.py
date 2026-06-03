from __future__ import annotations

import shutil
import sys
import sysconfig
from pathlib import Path


def _candidate_script_dirs() -> list[Path]:
    dirs: list[Path] = []
    seen: set[Path] = set()

    def add(path: Path) -> None:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            dirs.append(resolved)

    scripts = sysconfig.get_path("scripts")
    if scripts:
        add(Path(scripts))

    add(Path(sys.executable).parent)
    return dirs


def resolve_cli_executable(command: str) -> str | None:
    """Locate a CLI on PATH or in the active interpreter's script directory."""
    if executable := shutil.which(command):
        return executable

    suffixes = (".exe", "") if sys.platform == "win32" else ("",)
    for directory in _candidate_script_dirs():
        for suffix in suffixes:
            candidate = directory / f"{command}{suffix}"
            if candidate.is_file():
                return str(candidate)
    return None

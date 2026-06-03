from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.install_smoke
def test_install_smoke_from_built_wheel() -> None:
    root = Path(__file__).resolve().parents[2]
    script = root / "scripts" / "install_smoke_check.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=root,
        check=False,
    )
    assert result.returncode == 0, "install_smoke_check.py failed; see stderr above"

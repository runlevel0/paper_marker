from __future__ import annotations

import subprocess
import time
from pathlib import Path

from paper_marker.core.models import CandidateMetrics, CandidateResult, RouteStatus
from paper_marker.routes.base import ConversionRoute
from paper_marker.routes.cli_discovery import resolve_cli_executable

_MINERU_CLI_NAMES = ("mineru", "magic-pdf")


def _resolve_mineru_cli() -> tuple[str, str] | None:
    """Return (executable path, CLI name) for MinerU / legacy magic-pdf."""
    for cli_name in _MINERU_CLI_NAMES:
        if executable := resolve_cli_executable(cli_name):
            return executable, cli_name
    return None


class MinerURoute(ConversionRoute):
    name = "mineru"

    def is_available(self) -> tuple[bool, str]:
        resolved = _resolve_mineru_cli()
        if resolved:
            executable, cli_name = resolved
            return True, f"Found {cli_name} CLI at {executable}"
        return False, "mineru or magic-pdf CLI not found on PATH or in the paper-marker environment"

    def convert(self, pdf_path: Path, work_dir: Path, timeout_s: int) -> CandidateResult:
        start = time.perf_counter()
        out_dir = work_dir / self.name
        out_dir.mkdir(parents=True, exist_ok=True)
        resolved = _resolve_mineru_cli()
        if not resolved:
            return CandidateResult(
                route_name=self.name,
                status="unavailable",
                error="mineru or magic-pdf CLI not found on PATH or in the paper-marker environment",
                elapsed_s=time.perf_counter() - start,
            )
        executable, _cli_name = resolved
        cmd = [executable, "-p", str(pdf_path), "-o", str(out_dir)]
        try:
            completed = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout_s,
            )
            markdown_text = ""
            markdown_files = sorted(out_dir.glob("*.md"))
            if markdown_files:
                markdown_text = markdown_files[0].read_text(encoding="utf-8", errors="ignore")
            status: RouteStatus = "ok" if completed.returncode == 0 else "error"
            error = None if status == "ok" else completed.stderr[-2000:]
            metrics = CandidateMetrics.from_markdown(markdown_text) if markdown_text else None
            return CandidateResult(
                route_name=self.name,
                status=status,
                markdown_text=markdown_text,
                elapsed_s=time.perf_counter() - start,
                metrics=metrics,
                metadata={
                    "command": cmd,
                    "stdout_tail": completed.stdout[-2000:],
                    "stderr_tail": completed.stderr[-2000:],
                    "return_code": completed.returncode,
                    "output_dir": str(out_dir),
                },
                error=error,
            )
        except subprocess.TimeoutExpired:
            return CandidateResult(
                route_name=self.name,
                status="timeout",
                error=f"Route timed out after {timeout_s}s",
                elapsed_s=time.perf_counter() - start,
                metadata={"command": cmd},
            )

from __future__ import annotations

import subprocess
import time
from pathlib import Path

from paper_marker.core.models import CandidateMetrics, CandidateResult
from paper_marker.routes.base import ConversionRoute
from paper_marker.routes.cli_discovery import resolve_cli_executable


class NougatRoute(ConversionRoute):
    name = "nougat"

    def is_available(self) -> tuple[bool, str]:
        executable = resolve_cli_executable("nougat")
        if executable:
            return True, f"Found nougat CLI at {executable}"
        return False, "nougat CLI not found on PATH or in the paper-marker environment"

    def convert(self, pdf_path: Path, work_dir: Path, timeout_s: int) -> CandidateResult:
        start = time.perf_counter()
        out_dir = work_dir / self.name
        out_dir.mkdir(parents=True, exist_ok=True)
        executable = resolve_cli_executable("nougat")
        if not executable:
            return CandidateResult(
                route_name=self.name,
                status="unavailable",
                error="nougat CLI not found on PATH or in the paper-marker environment",
                elapsed_s=time.perf_counter() - start,
            )
        cmd = [executable, str(pdf_path), "-o", str(out_dir), "--markdown"]
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
            status = "ok" if completed.returncode == 0 else "error"
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

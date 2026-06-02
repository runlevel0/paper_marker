from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path

from paper_marker.core.models import CandidateMetrics, CandidateResult
from paper_marker.routes.base import ConversionRoute


class MarkItDownRoute(ConversionRoute):
    name = "markitdown"

    def is_available(self) -> tuple[bool, str]:
        executable = shutil.which("markitdown")
        if executable:
            return True, f"Found markitdown CLI at {executable}"
        return False, "markitdown CLI not found in PATH"

    def convert(self, pdf_path: Path, work_dir: Path, timeout_s: int) -> CandidateResult:
        start = time.perf_counter()
        out_dir = work_dir / self.name
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / "markitdown.md"
        cmd = ["markitdown", str(pdf_path)]
        try:
            completed = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout_s,
            )
            markdown_text = completed.stdout if completed.returncode == 0 else ""
            if markdown_text:
                out_file.write_text(markdown_text, encoding="utf-8")
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
                    "output_file": str(out_file),
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

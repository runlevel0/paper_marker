from __future__ import annotations

from pathlib import Path
from typing import Any

from typer.testing import CliRunner

from paper_marker.cli import app
from paper_marker.mcp import server as mcp_server


def test_cli_list_routes_runs() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["list-routes"])
    assert result.exit_code == 0
    assert "route" in result.stdout


def test_cli_convert_flag_for_candidate_bundle(monkeypatch: Any, tmp_path: Path) -> None:
    from paper_marker import cli as cli_module
    from paper_marker.core.models import FinalResult

    class DummyOrchestrator:
        def __init__(self, settings: Any):
            _ = settings
            self.captured_request = None

        def run(self, request: Any) -> FinalResult:
            self.captured_request = request
            return FinalResult(
                input_pdf=str(request.pdf_path),
                output_dir=str(request.out_dir),
                candidate_results=[],
                selected_route="best guess",
                selected_markdown_path=None,
                bundle_dir=None,
            )

    dummy = DummyOrchestrator(settings=None)
    monkeypatch.setattr(cli_module, "ConversionOrchestrator", lambda settings: dummy)

    pdf_path = tmp_path / "doc.pdf"
    pdf_path.write_text("dummy", encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["convert", str(pdf_path), "--out-dir", str(tmp_path / "out"), "--no-candidate-bundle"],
    )
    assert result.exit_code == 0
    assert dummy.captured_request is not None
    assert dummy.captured_request.export_candidate_bundle is False


def test_mcp_convert_tool_reuses_pipeline(monkeypatch: Any, tmp_path: Path) -> None:
    class DummyOrchestrator:
        def __init__(self, settings: Any):
            _ = settings

        def run(self, request: Any) -> Any:
            class _Result:
                def to_json_dict(self) -> dict[str, Any]:
                    return {
                        "input_pdf": str(request.pdf_path),
                        "output_dir": str(request.out_dir),
                        "selection_reason": "best guess",
                    }

            return _Result()

    monkeypatch.setattr(
        mcp_server, "ConversionOrchestrator", lambda settings: DummyOrchestrator(settings)
    )
    payload = mcp_server.convert_pdf_to_markdown(
        pdf_path=str(tmp_path / "paper.pdf"),
        out_dir=str(tmp_path / "out"),
        export_candidate_bundle=False,
    )
    assert payload["selection_reason"] == "best guess"

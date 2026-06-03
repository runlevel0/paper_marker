from __future__ import annotations

import inspect
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


def test_cli_convert_requires_out_dir(tmp_path: Path) -> None:
    pdf_path = tmp_path / "doc.pdf"
    pdf_path.write_text("dummy", encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(app, ["convert", str(pdf_path)])
    assert result.exit_code != 0
    assert "out-dir" in result.output.lower() or "out_dir" in result.output.lower()


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


def test_cli_convert_keep_temp_flag(monkeypatch: Any, tmp_path: Path) -> None:
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
        ["convert", str(pdf_path), "--out-dir", str(tmp_path / "out"), "--keep-temp"],
    )
    assert result.exit_code == 0
    assert dummy.captured_request is not None
    assert dummy.captured_request.keep_temp is True


def test_mcp_convert_tool_reuses_pipeline(monkeypatch: Any, tmp_path: Path) -> None:
    captured: dict[str, Any] = {}

    class DummyOrchestrator:
        def __init__(self, settings: Any):
            _ = settings

        def run(self, request: Any) -> Any:
            captured["request"] = request

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
        keep_temp=True,
    )
    assert payload["selection_reason"] == "best guess"
    assert captured["request"].keep_temp is True


def test_mcp_convert_requires_out_dir_parameter() -> None:
    signature = inspect.signature(mcp_server.convert_pdf_to_markdown)
    out_dir = signature.parameters["out_dir"]
    assert out_dir.default is inspect.Parameter.empty

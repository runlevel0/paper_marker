from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from paper_marker.config import AppSettings
from paper_marker.core.models import CandidateResult, ConversionRequest, SynthesisResult
from paper_marker.core.pipeline import ConversionOrchestrator


class _DummyFuture:
    def __init__(self, payload: dict[str, Any]):
        self._payload = payload

    def result(self, timeout: int | None = None) -> dict[str, Any]:
        _ = timeout
        return self._payload


class _ErrorFuture(_DummyFuture):
    def __init__(self, message: str):
        self._message = message

    def result(self, timeout: int | None = None) -> dict[str, Any]:
        _ = timeout
        raise RuntimeError(self._message)


class _DummyExecutor:
    def __init__(self, max_workers: int):
        self.max_workers = max_workers
        self.futures: list[_DummyFuture] = []

    def __enter__(self) -> _DummyExecutor:
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        _ = (exc_type, exc, tb)

    def submit(
        self, fn: Any, route_name: str, pdf_path: str, work_dir: str, timeout_s: int
    ) -> _DummyFuture:
        payload = fn(route_name, pdf_path, work_dir, timeout_s)
        future = _DummyFuture(payload)
        self.futures.append(future)
        return future


class _FailingExecutor(_DummyExecutor):
    def submit(
        self, fn: Any, route_name: str, pdf_path: str, work_dir: str, timeout_s: int
    ) -> _DummyFuture:
        _ = (fn, pdf_path, work_dir, timeout_s)
        future = _ErrorFuture(f"boom for {route_name}")
        self.futures.append(future)
        return future


def test_orchestrator_writes_flat_route_markdown(monkeypatch: Any, tmp_path: Path) -> None:
    import paper_marker.core.pipeline as pipeline_module

    def _successful_worker(
        route_name: str, pdf_path: str, work_dir: str, timeout_s: int
    ) -> dict[str, Any]:
        _ = (pdf_path, work_dir, timeout_s)
        return CandidateResult(
            route_name=route_name,
            status="ok",
            markdown_text="# converted",
        ).to_json_dict()

    monkeypatch.setattr(pipeline_module, "ProcessPoolExecutor", _DummyExecutor)
    monkeypatch.setattr(pipeline_module, "as_completed", lambda futures: futures)
    monkeypatch.setattr(pipeline_module, "_run_route_worker", _successful_worker)

    request = ConversionRequest(
        pdf_path=tmp_path / "input.pdf",
        out_dir=tmp_path / "out",
        routes=["markitdown"],
        timeout_per_route_s=10,
        synthesize=False,
    )
    request.pdf_path.write_text("fake pdf", encoding="utf-8")

    orchestrator = ConversionOrchestrator(settings=AppSettings())
    result = orchestrator.run(request)

    route_md = request.out_dir / "markitdown.md"
    assert route_md.exists()
    assert route_md.read_text(encoding="utf-8") == "# converted"
    assert result.route_markdown_paths == {"markitdown": str(route_md)}
    assert result.selected_markdown_path == str(route_md)
    assert result.selection_reason == "best guess"
    assert result.elapsed_s >= 0.0
    assert not (request.out_dir / "final.md").exists()
    assert not (request.out_dir / "run_report.json").exists()
    assert not (request.out_dir / "final_result.json").exists()
    assert not (request.out_dir / "candidate_bundle").exists()


def test_orchestrator_writes_one_markdown_per_successful_route(
    monkeypatch: Any, tmp_path: Path
) -> None:
    import paper_marker.core.pipeline as pipeline_module

    def _successful_worker(
        route_name: str, pdf_path: str, work_dir: str, timeout_s: int
    ) -> dict[str, Any]:
        _ = (pdf_path, work_dir, timeout_s)
        return CandidateResult(
            route_name=route_name,
            status="ok",
            markdown_text=f"# {route_name}",
        ).to_json_dict()

    monkeypatch.setattr(pipeline_module, "ProcessPoolExecutor", _DummyExecutor)
    monkeypatch.setattr(pipeline_module, "as_completed", lambda futures: futures)
    monkeypatch.setattr(pipeline_module, "_run_route_worker", _successful_worker)

    request = ConversionRequest(
        pdf_path=tmp_path / "input.pdf",
        out_dir=tmp_path / "out",
        routes=["markitdown", "marker"],
        timeout_per_route_s=10,
        synthesize=False,
    )
    request.pdf_path.write_text("fake pdf", encoding="utf-8")

    orchestrator = ConversionOrchestrator(settings=AppSettings())
    result = orchestrator.run(request)

    assert (request.out_dir / "markitdown.md").exists()
    assert (request.out_dir / "marker.md").exists()
    assert len(result.route_markdown_paths) == 2


def test_orchestrator_skips_markdown_for_failed_routes(monkeypatch: Any, tmp_path: Path) -> None:
    import paper_marker.core.pipeline as pipeline_module

    def _failing_worker(
        route_name: str, pdf_path: str, work_dir: str, timeout_s: int
    ) -> dict[str, Any]:
        _ = (pdf_path, work_dir, timeout_s)
        return CandidateResult(
            route_name=route_name,
            status="error",
            error="forced failure",
        ).to_json_dict()

    monkeypatch.setattr(pipeline_module, "ProcessPoolExecutor", _DummyExecutor)
    monkeypatch.setattr(pipeline_module, "as_completed", lambda futures: futures)
    monkeypatch.setattr(pipeline_module, "_run_route_worker", _failing_worker)

    request = ConversionRequest(
        pdf_path=tmp_path / "input.pdf",
        out_dir=tmp_path / "out",
        routes=["markitdown"],
        timeout_per_route_s=10,
        synthesize=False,
    )
    request.pdf_path.write_text("fake pdf", encoding="utf-8")

    orchestrator = ConversionOrchestrator(settings=AppSettings())
    result = orchestrator.run(request)

    assert not (request.out_dir / "markitdown.md").exists()
    assert result.route_markdown_paths == {}


def test_orchestrator_writes_synthesized_md_when_synthesize(
    monkeypatch: Any, tmp_path: Path
) -> None:
    import paper_marker.core.pipeline as pipeline_module

    def _successful_worker(
        route_name: str, pdf_path: str, work_dir: str, timeout_s: int
    ) -> dict[str, Any]:
        _ = (pdf_path, work_dir, timeout_s)
        return CandidateResult(
            route_name=route_name,
            status="ok",
            markdown_text="# route output",
        ).to_json_dict()

    def _fake_synthesize(
        candidates: list[CandidateResult],
        *,
        settings: AppSettings,
        model: str | None = None,
    ) -> SynthesisResult:
        _ = (candidates, settings, model)
        return SynthesisResult(
            markdown_text="# merged",
            model="test/model",
            provider="test",
            prompt_version="v1",
        )

    monkeypatch.setattr(pipeline_module, "ProcessPoolExecutor", _DummyExecutor)
    monkeypatch.setattr(pipeline_module, "as_completed", lambda futures: futures)
    monkeypatch.setattr(pipeline_module, "_run_route_worker", _successful_worker)
    monkeypatch.setattr(pipeline_module, "synthesize_candidates", _fake_synthesize)

    request = ConversionRequest(
        pdf_path=tmp_path / "input.pdf",
        out_dir=tmp_path / "out",
        routes=["markitdown"],
        timeout_per_route_s=10,
        synthesize=True,
    )
    request.pdf_path.write_text("fake pdf", encoding="utf-8")

    orchestrator = ConversionOrchestrator(settings=AppSettings())
    result = orchestrator.run(request)

    assert (request.out_dir / "markitdown.md").exists()
    synthesized = request.out_dir / "synthesized.md"
    assert synthesized.exists()
    assert synthesized.read_text(encoding="utf-8") == "# merged"
    assert result.selected_route == "synthesized"
    assert result.selected_markdown_path == str(synthesized)
    assert result.selection_reason == "llm synthesis"


def test_orchestrator_keeps_work_dir_when_requested(monkeypatch: Any, tmp_path: Path) -> None:
    import paper_marker.core.pipeline as pipeline_module

    monkeypatch.setattr(pipeline_module, "ProcessPoolExecutor", _DummyExecutor)
    monkeypatch.setattr(pipeline_module, "as_completed", lambda futures: futures)

    request = ConversionRequest(
        pdf_path=tmp_path / "input.pdf",
        out_dir=tmp_path / "out",
        routes=["markitdown"],
        timeout_per_route_s=10,
        synthesize=False,
        keep_temp=True,
    )
    request.pdf_path.write_text("fake pdf", encoding="utf-8")

    orchestrator = ConversionOrchestrator(settings=AppSettings())
    _ = orchestrator.run(request)

    assert (request.out_dir / "_work").exists()


def test_orchestrator_rejects_unknown_route(monkeypatch: Any, tmp_path: Path) -> None:
    import paper_marker.core.pipeline as pipeline_module

    monkeypatch.setattr(pipeline_module, "ProcessPoolExecutor", _DummyExecutor)
    monkeypatch.setattr(pipeline_module, "as_completed", lambda futures: futures)

    request = ConversionRequest(
        pdf_path=tmp_path / "input.pdf",
        out_dir=tmp_path / "out",
        routes=["does-not-exist"],
        timeout_per_route_s=10,
        synthesize=False,
    )
    request.pdf_path.write_text("fake pdf", encoding="utf-8")

    orchestrator = ConversionOrchestrator(settings=AppSettings())
    with pytest.raises(ValueError, match="Unknown routes"):
        orchestrator.run(request)


def test_orchestrator_attributes_worker_failure_to_route(monkeypatch: Any, tmp_path: Path) -> None:
    import paper_marker.core.pipeline as pipeline_module

    monkeypatch.setattr(pipeline_module, "ProcessPoolExecutor", _FailingExecutor)
    monkeypatch.setattr(pipeline_module, "as_completed", lambda futures: futures)

    request = ConversionRequest(
        pdf_path=tmp_path / "input.pdf",
        out_dir=tmp_path / "out",
        routes=["markitdown"],
        timeout_per_route_s=10,
        synthesize=False,
    )
    request.pdf_path.write_text("fake pdf", encoding="utf-8")

    orchestrator = ConversionOrchestrator(settings=AppSettings())
    result = orchestrator.run(request)

    assert len(result.candidate_results) == 1
    assert result.candidate_results[0].route_name == "markitdown"
    assert result.candidate_results[0].status == "error"
    assert "boom for markitdown" in (result.candidate_results[0].error or "")


def test_orchestrator_reports_all_routes_failed(monkeypatch: Any, tmp_path: Path) -> None:
    import paper_marker.core.pipeline as pipeline_module

    def _failing_worker(
        route_name: str, pdf_path: str, work_dir: str, timeout_s: int
    ) -> dict[str, Any]:
        _ = (pdf_path, work_dir, timeout_s)
        return CandidateResult(
            route_name=route_name,
            status="error",
            error="forced failure",
        ).to_json_dict()

    monkeypatch.setattr(pipeline_module, "ProcessPoolExecutor", _DummyExecutor)
    monkeypatch.setattr(pipeline_module, "as_completed", lambda futures: futures)
    monkeypatch.setattr(pipeline_module, "_run_route_worker", _failing_worker)

    request = ConversionRequest(
        pdf_path=tmp_path / "input.pdf",
        out_dir=tmp_path / "out",
        routes=["markitdown"],
        timeout_per_route_s=10,
        synthesize=False,
    )
    request.pdf_path.write_text("fake pdf", encoding="utf-8")

    orchestrator = ConversionOrchestrator(settings=AppSettings())
    result = orchestrator.run(request)

    assert result.selection_reason == "all routes failed"
    assert result.selected_route == "none"
    assert result.selected_markdown_path is None
    assert not (request.out_dir / "final.md").exists()
    assert not (request.out_dir / "synthesized.md").exists()

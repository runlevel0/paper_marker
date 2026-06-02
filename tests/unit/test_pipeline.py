from __future__ import annotations

from pathlib import Path
from typing import Any

from paper_marker.config import AppSettings
from paper_marker.core.models import ConversionRequest
from paper_marker.core.pipeline import ConversionOrchestrator


class _DummyFuture:
    def __init__(self, payload: dict[str, Any]):
        self._payload = payload

    def result(self, timeout: int | None = None) -> dict[str, Any]:
        _ = timeout
        return self._payload


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


def test_orchestrator_writes_candidate_bundle_and_best_guess(
    monkeypatch: Any, tmp_path: Path
) -> None:
    import paper_marker.core.pipeline as pipeline_module

    monkeypatch.setattr(pipeline_module, "ProcessPoolExecutor", _DummyExecutor)
    monkeypatch.setattr(pipeline_module, "as_completed", lambda futures: futures)

    request = ConversionRequest(
        pdf_path=tmp_path / "input.pdf",
        out_dir=tmp_path / "out",
        routes=["markitdown"],
        timeout_per_route_s=10,
        synthesize=False,
        export_candidate_bundle=True,
    )
    request.pdf_path.write_text("fake pdf", encoding="utf-8")

    orchestrator = ConversionOrchestrator(settings=AppSettings())
    result = orchestrator.run(request)

    assert result.selection_reason == "best guess"
    assert result.bundle_dir is not None
    assert (Path(result.output_dir) / "candidate_bundle").exists()
    assert (Path(result.output_dir) / "run_report.json").exists()


def test_orchestrator_allows_disabling_candidate_bundle(monkeypatch: Any, tmp_path: Path) -> None:
    import paper_marker.core.pipeline as pipeline_module

    monkeypatch.setattr(pipeline_module, "ProcessPoolExecutor", _DummyExecutor)
    monkeypatch.setattr(pipeline_module, "as_completed", lambda futures: futures)

    request = ConversionRequest(
        pdf_path=tmp_path / "input.pdf",
        out_dir=tmp_path / "out",
        routes=["markitdown"],
        timeout_per_route_s=10,
        synthesize=False,
        export_candidate_bundle=False,
    )
    request.pdf_path.write_text("fake pdf", encoding="utf-8")

    orchestrator = ConversionOrchestrator(settings=AppSettings())
    result = orchestrator.run(request)

    assert result.bundle_dir is None
    assert not (Path(result.output_dir) / "candidate_bundle").exists()

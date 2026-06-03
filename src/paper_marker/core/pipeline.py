from __future__ import annotations

import shutil
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from paper_marker.config import AppSettings
from paper_marker.core.models import (
    CandidateMetrics,
    CandidateResult,
    ConversionRequest,
    FinalResult,
)
from paper_marker.routes import ROUTE_REGISTRY
from paper_marker.routes.base import ConversionRoute
from paper_marker.synthesis.openrouter_synth import synthesize_candidates


def _run_route_worker(
    route_name: str, pdf_path: str, work_dir: str, timeout_s: int
) -> dict[str, Any]:
    route_class = ROUTE_REGISTRY[route_name]
    route: ConversionRoute = route_class()
    available, reason = route.is_available()
    if not available:
        result = CandidateResult(
            route_name=route_name,
            status="unavailable",
            error=reason,
            metadata={"availability_note": reason},
        )
        return result.to_json_dict()
    result = route.convert(Path(pdf_path), Path(work_dir), timeout_s)
    if result.metrics is None and result.markdown_text:
        result.metrics = CandidateMetrics.from_markdown(result.markdown_text)
    return result.to_json_dict()


def _score_candidate(candidate: CandidateResult) -> float:
    if candidate.status != "ok" or not candidate.metrics:
        return -1.0
    return (
        candidate.metrics.markdown_chars * 0.001
        + candidate.metrics.heading_count * 2.0
        + candidate.metrics.formula_markers * 0.5
    )


def _from_dict(data: dict[str, Any]) -> CandidateResult:
    metrics_payload = data.get("metrics")
    metrics = CandidateMetrics(**metrics_payload) if metrics_payload else None
    return CandidateResult(
        route_name=data["route_name"],
        status=data["status"],
        markdown_text=data.get("markdown_text", ""),
        assets=data.get("assets", []),
        error=data.get("error"),
        elapsed_s=data.get("elapsed_s", 0.0),
        metrics=metrics,
        metadata=data.get("metadata", {}),
    )


def _write_route_markdown(out_dir: Path, candidate: CandidateResult) -> Path | None:
    if candidate.status != "ok" or not candidate.markdown_text:
        return None
    path = out_dir / f"{candidate.route_name}.md"
    path.write_text(candidate.markdown_text, encoding="utf-8")
    return path


class ConversionOrchestrator:
    def __init__(self, settings: AppSettings):
        self.settings = settings

    def list_routes(self) -> list[dict[str, Any]]:
        details: list[dict[str, Any]] = []
        for route_name, route_class in ROUTE_REGISTRY.items():
            route = route_class()
            available, note = route.is_available()
            details.append({"route": route_name, "available": available, "note": note})
        return details

    def run(self, request: ConversionRequest) -> FinalResult:
        request.out_dir.mkdir(parents=True, exist_ok=True)
        work_dir = request.out_dir / "_work"
        work_dir.mkdir(parents=True, exist_ok=True)

        start = time.perf_counter()
        results: list[CandidateResult] = []
        if not request.routes:
            raise ValueError("At least one conversion route must be provided")
        unknown_routes = sorted(set(request.routes) - set(ROUTE_REGISTRY))
        if unknown_routes:
            known_routes = ", ".join(sorted(ROUTE_REGISTRY))
            unknown_display = ", ".join(unknown_routes)
            raise ValueError(f"Unknown routes: {unknown_display}. Known routes are: {known_routes}")
        max_workers = max(1, min(len(request.routes), self.settings.max_parallel_routes))
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            future_to_route = {
                executor.submit(
                    _run_route_worker,
                    route_name,
                    str(request.pdf_path),
                    str(work_dir),
                    request.timeout_per_route_s,
                ): route_name
                for route_name in request.routes
            }
            for future in as_completed(list(future_to_route)):
                route_name = future_to_route[future]
                try:
                    data = future.result(timeout=request.timeout_per_route_s + 30)
                    results.append(_from_dict(data))
                except Exception as exc:  # noqa: BLE001
                    results.append(
                        CandidateResult(
                            route_name=route_name,
                            status="error",
                            error=f"Worker failure: {exc}",
                        )
                    )

        route_markdown_paths: dict[str, str] = {}
        for candidate in results:
            path = _write_route_markdown(request.out_dir, candidate)
            if path is not None:
                route_markdown_paths[candidate.route_name] = str(path)

        ordered = sorted(results, key=_score_candidate, reverse=True)
        successful_candidates = [candidate for candidate in ordered if candidate.status == "ok"]
        best_guess = (
            successful_candidates[0]
            if successful_candidates
            else CandidateResult(route_name="none", status="error")
        )
        selected_route = best_guess.route_name
        selected_markdown_path: Path | None = None
        synthesis_result = None
        final_markdown = best_guess.markdown_text
        selection_reason = "best guess" if successful_candidates else "all routes failed"

        if request.synthesize:
            if not successful_candidates:
                selected_route = "none"
                final_markdown = ""
            else:
                synthesis_result = synthesize_candidates(
                    successful_candidates,
                    settings=self.settings,
                    model=request.openrouter_model,
                )
                final_markdown = synthesis_result.markdown_text
                selected_route = "synthesized"
                selection_reason = "llm synthesis"
                if final_markdown:
                    selected_markdown_path = request.out_dir / "synthesized.md"
                    selected_markdown_path.write_text(final_markdown, encoding="utf-8")
        elif best_guess.route_name in route_markdown_paths:
            selected_markdown_path = Path(route_markdown_paths[best_guess.route_name])

        elapsed_s = time.perf_counter() - start
        final_result = FinalResult(
            input_pdf=str(request.pdf_path),
            output_dir=str(request.out_dir),
            candidate_results=results,
            selected_route=selected_route,
            selected_markdown_path=str(selected_markdown_path) if selected_markdown_path else None,
            route_markdown_paths=route_markdown_paths,
            synthesis_result=synthesis_result,
            selection_reason=selection_reason,
            elapsed_s=elapsed_s,
        )
        if not request.keep_temp:
            shutil.rmtree(work_dir, ignore_errors=True)
        return final_result

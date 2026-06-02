"""Domain runtime models are dataclass-based by policy.

Pydantic is reserved for configuration/env parsing in `paper_marker.config`.
See `docs/modeling_policy.md` for details.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

RouteStatus = Literal["ok", "error", "timeout", "unavailable"]


@dataclass(slots=True)
class CandidateMetrics:
    markdown_chars: int
    heading_count: int
    formula_markers: int

    @classmethod
    def from_markdown(cls, markdown_text: str) -> CandidateMetrics:
        heading_count = sum(
            1 for line in markdown_text.splitlines() if line.lstrip().startswith("#")
        )
        formula_markers = markdown_text.count("$")
        return cls(
            markdown_chars=len(markdown_text),
            heading_count=heading_count,
            formula_markers=formula_markers,
        )


@dataclass(slots=True)
class CandidateResult:
    route_name: str
    status: RouteStatus
    markdown_text: str = ""
    assets: list[str] = field(default_factory=list)
    error: str | None = None
    elapsed_s: float = 0.0
    metrics: CandidateMetrics | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        return payload


@dataclass(slots=True)
class SynthesisResult:
    markdown_text: str
    model: str
    provider: str
    prompt_version: str
    usage: dict[str, Any] = field(default_factory=dict)
    prompt_budget: dict[str, Any] = field(default_factory=dict)
    raw_response: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class FinalResult:
    input_pdf: str
    output_dir: str
    candidate_results: list[CandidateResult]
    selected_route: str
    selected_markdown_path: str | None
    bundle_dir: str | None
    synthesis_result: SynthesisResult | None = None
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    selection_reason: str = "best guess"

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "input_pdf": self.input_pdf,
            "output_dir": self.output_dir,
            "candidate_results": [candidate.to_json_dict() for candidate in self.candidate_results],
            "selected_route": self.selected_route,
            "selected_markdown_path": self.selected_markdown_path,
            "bundle_dir": self.bundle_dir,
            "synthesis_result": asdict(self.synthesis_result) if self.synthesis_result else None,
            "created_at": self.created_at,
            "selection_reason": self.selection_reason,
        }


@dataclass(slots=True)
class ConversionRequest:
    pdf_path: Path
    out_dir: Path
    routes: list[str]
    timeout_per_route_s: int
    synthesize: bool
    export_candidate_bundle: bool = True
    keep_temp: bool = False
    openrouter_model: str | None = None

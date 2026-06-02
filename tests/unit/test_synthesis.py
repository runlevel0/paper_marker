from paper_marker.config import AppSettings
from paper_marker.core.models import CandidateMetrics, CandidateResult
from paper_marker.synthesis.openrouter_synth import build_synthesis_prompt


def test_build_synthesis_prompt_contains_candidates_and_rules() -> None:
    candidate = CandidateResult(
        route_name="marker",
        status="ok",
        markdown_text="# A\n\n$E=mc^2$",
        metrics=CandidateMetrics.from_markdown("# A\n\n$E=mc^2$"),
    )
    prompt, budget = build_synthesis_prompt([candidate], AppSettings())
    assert "Preserve math fidelity" in prompt
    assert "marker" in prompt
    assert "E=mc^2" in prompt
    assert budget["candidate_count_in_prompt"] == 1


def test_build_synthesis_prompt_applies_truncation_budget() -> None:
    first = CandidateResult(
        route_name="marker",
        status="ok",
        markdown_text="A" * 20,
        metrics=CandidateMetrics(markdown_chars=20, heading_count=0, formula_markers=0),
    )
    second = CandidateResult(
        route_name="nougat",
        status="ok",
        markdown_text="B" * 20,
        metrics=CandidateMetrics(markdown_chars=20, heading_count=0, formula_markers=0),
    )
    settings = AppSettings()
    settings.synth_max_chars_per_candidate = 10
    settings.synth_max_total_chars = 10
    prompt, budget = build_synthesis_prompt([first, second], settings)
    assert budget["truncated_candidates"] == ["marker"]
    assert budget["omitted_candidates"] == ["nougat"]
    assert budget["total_chars_in_prompt"] <= settings.synth_max_total_chars
    assert "...[trunca" in prompt

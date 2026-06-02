from paper_marker.core.models import CandidateMetrics, CandidateResult
from paper_marker.synthesis.openrouter_synth import build_synthesis_prompt


def test_build_synthesis_prompt_contains_candidates_and_rules() -> None:
    candidate = CandidateResult(
        route_name="marker",
        status="ok",
        markdown_text="# A\n\n$E=mc^2$",
        metrics=CandidateMetrics.from_markdown("# A\n\n$E=mc^2$"),
    )
    prompt = build_synthesis_prompt([candidate])
    assert "Preserve math fidelity" in prompt
    assert "marker" in prompt
    assert "E=mc^2" in prompt

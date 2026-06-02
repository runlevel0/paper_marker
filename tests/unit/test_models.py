from paper_marker.core.models import CandidateMetrics


def test_candidate_metrics_from_markdown_counts_expected_features() -> None:
    markdown = "# Title\n\nSome text with inline math $a+b$.\n\n## Section\n\n$$x^2$$"
    metrics = CandidateMetrics.from_markdown(markdown)
    assert metrics.markdown_chars == len(markdown)
    assert metrics.heading_count == 2
    assert metrics.formula_markers == 6

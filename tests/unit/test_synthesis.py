from __future__ import annotations

from typing import Any

import httpx
import pytest

from paper_marker.config import AppSettings
from paper_marker.core.models import CandidateMetrics, CandidateResult
from paper_marker.synthesis.openrouter_synth import build_synthesis_prompt, synthesize_candidates


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


class _FakeClient:
    def __init__(self, responses: list[httpx.Response]) -> None:
        self._responses = responses
        self.calls = 0

    def __enter__(self) -> _FakeClient:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        return None

    def post(self, url: str, json: dict[str, Any], headers: dict[str, str]) -> httpx.Response:
        del url, json, headers
        response = self._responses[self.calls]
        self.calls += 1
        return response


def _response(status_code: int, payload: dict[str, Any]) -> httpx.Response:
    request = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")
    return httpx.Response(status_code=status_code, json=payload, request=request)


def test_synthesize_candidates_retries_transient_http_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = AppSettings(
        OPENROUTER_API_KEY="test-key",
        PAPER_MARKER_SYNTH_HTTP_MAX_RETRIES=1,
        PAPER_MARKER_SYNTH_HTTP_BACKOFF_SECONDS=0,
    )
    first = _response(429, {"error": {"message": "rate limited"}})
    second = _response(
        200,
        {
            "choices": [{"message": {"content": "# merged"}}],
            "usage": {"total_tokens": 42},
        },
    )
    fake_client = _FakeClient([first, second])

    def _client_factory(*args: Any, **kwargs: Any) -> _FakeClient:
        del args, kwargs
        return fake_client

    monkeypatch.setattr(httpx, "Client", _client_factory)
    candidate = CandidateResult(
        route_name="marker",
        status="ok",
        markdown_text="# candidate",
        metrics=CandidateMetrics.from_markdown("# candidate"),
    )

    result = synthesize_candidates([candidate], settings)

    assert result.markdown_text == "# merged"
    assert fake_client.calls == 2


def test_synthesize_candidates_success_on_first_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = AppSettings(OPENROUTER_API_KEY="test-key")
    response = _response(
        200,
        {
            "choices": [{"message": {"content": "# synthesized"}}],
            "usage": {"total_tokens": 12},
        },
    )
    fake_client = _FakeClient([response])
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: fake_client)
    candidate = CandidateResult(
        route_name="marker",
        status="ok",
        markdown_text="# candidate",
        metrics=CandidateMetrics.from_markdown("# candidate"),
    )

    result = synthesize_candidates([candidate], settings, model="test/model")

    assert result.markdown_text == "# synthesized"
    assert result.model == "test/model"
    assert fake_client.calls == 1


def test_synthesize_candidates_raises_on_non_transient_http_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = AppSettings(
        OPENROUTER_API_KEY="test-key",
        PAPER_MARKER_SYNTH_HTTP_MAX_RETRIES=2,
        PAPER_MARKER_SYNTH_HTTP_BACKOFF_SECONDS=0,
    )
    fake_client = _FakeClient([_response(400, {"error": {"message": "bad request"}})])
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: fake_client)
    candidate = CandidateResult(
        route_name="marker",
        status="ok",
        markdown_text="# candidate",
        metrics=CandidateMetrics.from_markdown("# candidate"),
    )

    with pytest.raises(httpx.HTTPStatusError):
        synthesize_candidates([candidate], settings)

    assert fake_client.calls == 1


def test_synthesize_candidates_requires_api_key() -> None:
    settings = AppSettings()
    candidate = CandidateResult(route_name="marker", status="ok", markdown_text="# x")

    with pytest.raises(ValueError, match="no OPENROUTER_API_KEY"):
        synthesize_candidates([candidate], settings)

from __future__ import annotations

from dataclasses import asdict
from typing import Any

import httpx

from paper_marker.config import AppSettings
from paper_marker.core.models import CandidateResult, SynthesisResult

PROMPT_VERSION = "v1"


def build_synthesis_prompt(candidates: list[CandidateResult]) -> str:
    serialized_candidates = []
    for candidate in candidates:
        serialized_candidates.append(
            {
                "route_name": candidate.route_name,
                "status": candidate.status,
                "metrics": asdict(candidate.metrics) if candidate.metrics else None,
                "markdown_text": candidate.markdown_text,
            }
        )
    return (
        "You are merging scientific-paper markdown candidates.\n"
        "Rules:\n"
        "1) Preserve math fidelity and keep formulas in LaTeX.\n"
        "2) Do not hallucinate references, figures, or sections.\n"
        "3) Prefer better structure and readability.\n"
        "Return only synthesized markdown.\n\n"
        f"Candidates:\n{serialized_candidates}"
    )


def synthesize_candidates(
    candidates: list[CandidateResult], settings: AppSettings, model: str | None = None
) -> SynthesisResult:
    api_key = settings.resolved_api_key()
    if not api_key:
        raise ValueError("Synthesis requested but no OPENROUTER_API_KEY/OPENAI_API_KEY configured")

    selected_model = model or settings.default_openrouter_model
    url = f"{settings.openai_base_url.rstrip('/')}/chat/completions"
    payload: dict[str, Any] = {
        "model": selected_model,
        "messages": [
            {"role": "system", "content": "You are an expert scientific document editor."},
            {"role": "user", "content": build_synthesis_prompt(candidates)},
        ],
        "temperature": 0.1,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    with httpx.Client(timeout=120.0) as client:
        response = client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    choice = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    return SynthesisResult(
        markdown_text=choice,
        model=selected_model,
        provider="openai-compatible",
        prompt_version=PROMPT_VERSION,
        usage=usage,
        raw_response=data,
    )

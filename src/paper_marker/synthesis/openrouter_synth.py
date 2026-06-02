from __future__ import annotations

from dataclasses import asdict
from typing import Any

import httpx

from paper_marker.config import AppSettings
from paper_marker.core.models import CandidateResult, SynthesisResult

PROMPT_VERSION = "v1"


def _truncate_text(text: str, max_chars: int) -> tuple[str, bool]:
    if max_chars <= 0:
        return "", True
    if len(text) <= max_chars:
        return text, False
    suffix = "...[truncated for synthesis budget]..."
    if max_chars <= len(suffix):
        return suffix[:max_chars], True
    keep = max_chars - len(suffix)
    return text[:keep] + suffix, True


def build_synthesis_prompt(
    candidates: list[CandidateResult], settings: AppSettings
) -> tuple[str, dict[str, Any]]:
    serialized_candidates = []
    total_chars = 0
    truncated_candidates: list[str] = []
    omitted_candidates: list[str] = []
    max_per_candidate = settings.synth_max_chars_per_candidate
    max_total = settings.synth_max_total_chars
    for candidate in candidates:
        truncated_markdown, was_truncated = _truncate_text(
            candidate.markdown_text, max_per_candidate
        )
        prospective_total = total_chars + len(truncated_markdown)
        if prospective_total > max_total:
            omitted_candidates.append(candidate.route_name)
            continue
        if was_truncated:
            truncated_candidates.append(candidate.route_name)
        total_chars = prospective_total
        serialized_candidates.append(
            {
                "route_name": candidate.route_name,
                "status": candidate.status,
                "metrics": asdict(candidate.metrics) if candidate.metrics else None,
                "markdown_text": truncated_markdown,
            }
        )
    prompt = (
        "You are merging scientific-paper markdown candidates.\n"
        "Rules:\n"
        "1) Preserve math fidelity and keep formulas in LaTeX.\n"
        "2) Do not hallucinate references, figures, or sections.\n"
        "3) Prefer better structure and readability.\n"
        "Return only synthesized markdown.\n\n"
        f"Candidates:\n{serialized_candidates}"
    )
    budget = {
        "max_chars_per_candidate": max_per_candidate,
        "max_total_chars": max_total,
        "total_chars_in_prompt": total_chars,
        "truncated_candidates": truncated_candidates,
        "omitted_candidates": omitted_candidates,
        "candidate_count_in_prompt": len(serialized_candidates),
    }
    return prompt, budget


def synthesize_candidates(
    candidates: list[CandidateResult], settings: AppSettings, model: str | None = None
) -> SynthesisResult:
    api_key = settings.resolved_api_key()
    if not api_key:
        raise ValueError("Synthesis requested but no OPENROUTER_API_KEY/OPENAI_API_KEY configured")

    selected_model = model or settings.default_openrouter_model
    prompt, prompt_budget = build_synthesis_prompt(candidates, settings)
    url = f"{settings.openai_base_url.rstrip('/')}/chat/completions"
    payload: dict[str, Any] = {
        "model": selected_model,
        "messages": [
            {"role": "system", "content": "You are an expert scientific document editor."},
            {"role": "user", "content": prompt},
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
        prompt_budget=prompt_budget,
        raw_response=data,
    )

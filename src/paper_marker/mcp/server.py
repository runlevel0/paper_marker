from __future__ import annotations

from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from paper_marker.config import load_settings
from paper_marker.core.models import ConversionRequest
from paper_marker.core.pipeline import ConversionOrchestrator
from paper_marker.routes import DEFAULT_ROUTES

mcp = FastMCP("paper-marker")


@mcp.tool()
def list_conversion_routes() -> list[dict[str, Any]]:
    """List registered conversion routes and whether each external CLI is on PATH."""
    settings = load_settings()
    orchestrator = ConversionOrchestrator(settings=settings)
    return orchestrator.list_routes()


@mcp.tool()
def validate_environment() -> dict[str, Any]:
    """Report route availability, API base URL, and whether synthesis credentials are set."""
    settings = load_settings()
    orchestrator = ConversionOrchestrator(settings=settings)
    return {
        "routes": orchestrator.list_routes(),
        "openai_base_url": settings.openai_base_url,
        "has_api_key": settings.resolved_api_key() is not None,
    }


@mcp.tool()
def convert_pdf_to_markdown(
    pdf_path: str,
    out_dir: str,
    routes: list[str] | None = None,
    timeout_per_route_s: int = 300,
    synthesize: bool = False,
    openrouter_model: str | None = None,
    export_candidate_bundle: bool = True,
    keep_temp: bool = False,
) -> dict[str, Any]:
    """Convert a PDF to Markdown using parallel routes; mirrors the paper-marker convert CLI.

    Args:
        pdf_path: Path to the input PDF file.
        out_dir: Output directory for final.md, JSON reports, and optional bundles (required).
        routes: Route names to run; defaults to marker, mineru, nougat, markitdown.
        timeout_per_route_s: Per-route subprocess timeout in seconds.
        synthesize: When true, merge successful candidates via OpenRouter/OpenAI-compatible API.
        openrouter_model: Optional synthesis model override (e.g. openrouter/auto).
        export_candidate_bundle: Write per-route artifacts under candidate_bundle/ when true.
        keep_temp: Retain intermediate route workspace under _work/ after the run when true.
    """
    settings = load_settings()
    orchestrator = ConversionOrchestrator(settings=settings)
    request = ConversionRequest(
        pdf_path=Path(pdf_path),
        out_dir=Path(out_dir),
        routes=routes or DEFAULT_ROUTES,
        timeout_per_route_s=timeout_per_route_s,
        synthesize=synthesize,
        export_candidate_bundle=export_candidate_bundle,
        keep_temp=keep_temp,
        openrouter_model=openrouter_model,
    )
    return orchestrator.run(request).to_json_dict()


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

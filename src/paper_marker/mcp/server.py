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
    settings = load_settings()
    orchestrator = ConversionOrchestrator(settings=settings)
    return orchestrator.list_routes()


@mcp.tool()
def validate_environment() -> dict[str, Any]:
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
    out_dir: str = "out",
    routes: list[str] | None = None,
    timeout_per_route_s: int = 300,
    synthesize: bool = False,
    openrouter_model: str | None = None,
    export_candidate_bundle: bool = True,
) -> dict[str, Any]:
    settings = load_settings()
    orchestrator = ConversionOrchestrator(settings=settings)
    request = ConversionRequest(
        pdf_path=Path(pdf_path),
        out_dir=Path(out_dir),
        routes=routes or DEFAULT_ROUTES,
        timeout_per_route_s=timeout_per_route_s,
        synthesize=synthesize,
        export_candidate_bundle=export_candidate_bundle,
        openrouter_model=openrouter_model,
    )
    return orchestrator.run(request).to_json_dict()


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

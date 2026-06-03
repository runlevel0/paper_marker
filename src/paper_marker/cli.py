from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from paper_marker.config import load_settings
from paper_marker.core.models import ConversionRequest
from paper_marker.core.pipeline import ConversionOrchestrator
from paper_marker.routes import DEFAULT_ROUTES

app = typer.Typer(no_args_is_help=True, help="Parallel scientific PDF to Markdown converter.")


@app.command("list-routes")
def list_routes() -> None:
    """List registered conversion routes and whether each CLI is available on PATH."""
    settings = load_settings()
    orchestrator = ConversionOrchestrator(settings=settings)
    typer.echo(json.dumps(orchestrator.list_routes(), indent=2))


@app.command("doctor")
def doctor() -> None:
    """Report route availability and whether synthesis API credentials are configured."""
    settings = load_settings()
    orchestrator = ConversionOrchestrator(settings=settings)
    route_status = orchestrator.list_routes()
    payload = {
        "routes": route_status,
        "openai_base_url": settings.openai_base_url,
        "has_api_key": settings.resolved_api_key() is not None,
    }
    typer.echo(json.dumps(payload, indent=2))


@app.command("convert")
def convert(
    pdf_path: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=False,
            help="Input PDF file to convert.",
        ),
    ],
    out_dir: Annotated[
        Path,
        typer.Option(
            "--out-dir",
            help="Output directory for per-route Markdown files and optional synthesized.md.",
        ),
    ],
    routes: Annotated[
        list[str] | None,
        typer.Option(
            "--routes",
            help=(
                "Route names to run (repeatable). Defaults to all: marker, mineru, nougat, "
                "markitdown."
            ),
        ),
    ] = None,
    timeout_per_route: Annotated[
        int,
        typer.Option(
            "--timeout-per-route",
            help="Per-route subprocess timeout in seconds (overrides env default).",
        ),
    ] = 300,
    synthesize: Annotated[
        bool,
        typer.Option(
            "--synthesize",
            help="Merge successful candidates via OpenRouter/OpenAI-compatible API.",
        ),
    ] = False,
    openrouter_model: Annotated[
        str | None,
        typer.Option(
            "--openrouter-model",
            help="Synthesis model override (e.g. openrouter/auto).",
        ),
    ] = None,
    keep_temp: Annotated[
        bool,
        typer.Option(
            "--keep-temp",
            help="Retain intermediate route workspace under _work/ after the run.",
        ),
    ] = False,
) -> None:
    """Run parallel PDF-to-Markdown conversion and write results under --out-dir."""
    settings = load_settings()
    orchestrator = ConversionOrchestrator(settings=settings)
    request = ConversionRequest(
        pdf_path=pdf_path,
        out_dir=out_dir,
        routes=routes or DEFAULT_ROUTES,
        timeout_per_route_s=timeout_per_route,
        synthesize=synthesize,
        keep_temp=keep_temp,
        openrouter_model=openrouter_model,
    )
    result = orchestrator.run(request)
    typer.echo(json.dumps(result.to_json_dict(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    app()

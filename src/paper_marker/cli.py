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
    settings = load_settings()
    orchestrator = ConversionOrchestrator(settings=settings)
    typer.echo(json.dumps(orchestrator.list_routes(), indent=2))


@app.command("doctor")
def doctor() -> None:
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
    pdf_path: Annotated[Path, typer.Argument(exists=True, file_okay=True, dir_okay=False)],
    out_dir: Annotated[Path, typer.Option("--out-dir")] = Path("out"),
    routes: Annotated[list[str] | None, typer.Option("--routes")] = None,
    timeout_per_route: Annotated[int, typer.Option("--timeout-per-route")] = 300,
    synthesize: Annotated[bool, typer.Option("--synthesize")] = False,
    openrouter_model: Annotated[str | None, typer.Option("--openrouter-model")] = None,
    export_candidate_bundle: Annotated[
        bool, typer.Option("--export-candidate-bundle/--no-candidate-bundle")
    ] = True,
    keep_temp: Annotated[bool, typer.Option("--keep-temp")] = False,
) -> None:
    settings = load_settings()
    orchestrator = ConversionOrchestrator(settings=settings)
    request = ConversionRequest(
        pdf_path=pdf_path,
        out_dir=out_dir,
        routes=routes or DEFAULT_ROUTES,
        timeout_per_route_s=timeout_per_route,
        synthesize=synthesize,
        export_candidate_bundle=export_candidate_bundle,
        keep_temp=keep_temp,
        openrouter_model=openrouter_model,
    )
    result = orchestrator.run(request)
    typer.echo(json.dumps(result.to_json_dict(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    app()

"""Build (or accept) a wheel, install into a clean venv, and exercise console entry points."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import anyio
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

EXPECTED_TOOLS = {"list_conversion_routes", "validate_environment", "convert_pdf_to_markdown"}


def _run(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        msg = (
            f"Command failed ({result.returncode}): {' '.join(cmd)}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
        raise RuntimeError(msg)
    return result


def _resolve_wheel(*, root: Path, wheel: Path | None, dist_dir: Path | None) -> Path:
    if wheel is not None:
        if not wheel.is_file():
            raise FileNotFoundError(f"Wheel not found: {wheel}")
        return wheel.resolve()
    if dist_dir is not None:
        wheels = sorted(dist_dir.glob("*.whl"), key=lambda path: path.stat().st_mtime)
        if not wheels:
            raise FileNotFoundError(f"No wheel in {dist_dir}")
        return wheels[-1].resolve()
    return _build_wheel(root)


def _build_wheel(root: Path) -> Path:
    dist = root / "dist"
    if dist.exists():
        shutil.rmtree(dist)
    dist.mkdir(parents=True)
    uv = shutil.which("uv")
    if uv:
        _run([uv, "build", "--wheel", "--out-dir", str(dist)], cwd=root)
    else:
        _run([sys.executable, "-m", "pip", "install", "--quiet", "build"], cwd=root)
        _run([sys.executable, "-m", "build", "--wheel", "--outdir", str(dist)], cwd=root)
    wheels = sorted(dist.glob("*.whl"), key=lambda path: path.stat().st_mtime)
    if not wheels:
        raise RuntimeError(f"No wheel produced under {dist}")
    return wheels[-1].resolve()


def _venv_paths(venv_dir: Path) -> tuple[Path, Path]:
    if sys.platform == "win32":
        return venv_dir / "Scripts" / "python.exe", venv_dir / "Scripts"
    return venv_dir / "bin" / "python", venv_dir / "bin"


def _script_path(scripts_dir: Path, name: str) -> Path:
    if sys.platform == "win32":
        return scripts_dir / f"{name}.exe"
    return scripts_dir / name


async def _mcp_tools_list(mcp_command: list[str], cwd: Path) -> None:
    params = StdioServerParameters(command=mcp_command[0], args=mcp_command[1:], cwd=cwd)
    async with (
        stdio_client(params) as (read_stream, write_stream),
        ClientSession(read_stream, write_stream) as session,
    ):
        await session.initialize()
        tools = await session.list_tools()
        names = {tool.name for tool in tools.tools}
        missing = EXPECTED_TOOLS - names
        if missing:
            raise RuntimeError(f"Missing expected MCP tools: {sorted(missing)}")


def run_install_smoke(
    *,
    root: Path,
    wheel: Path | None = None,
    dist_dir: Path | None = None,
) -> None:
    resolved_wheel = _resolve_wheel(root=root, wheel=wheel, dist_dir=dist_dir)
    with tempfile.TemporaryDirectory(prefix="paper-marker-install-smoke-") as tmp:
        venv_dir = Path(tmp) / "venv"
        _run([sys.executable, "-m", "venv", str(venv_dir)])
        venv_python, scripts_dir = _venv_paths(venv_dir)
        _run([str(venv_python), "-m", "pip", "install", "--quiet", str(resolved_wheel)])

        env = os.environ.copy()
        env["PATH"] = str(scripts_dir) + os.pathsep + env.get("PATH", "")

        paper_marker = _script_path(scripts_dir, "paper-marker")
        paper_marker_mcp = _script_path(scripts_dir, "paper-marker-mcp")
        if not paper_marker.is_file():
            raise RuntimeError(f"Console script missing after install: {paper_marker}")
        if not paper_marker_mcp.is_file():
            raise RuntimeError(f"Console script missing after install: {paper_marker_mcp}")

        _run([str(paper_marker), "--help"], cwd=root, env=env)
        list_routes = _run([str(paper_marker), "list-routes"], cwd=root, env=env)
        if not list_routes.stdout.strip():
            raise RuntimeError("paper-marker list-routes produced empty stdout")

        anyio.run(_mcp_tools_list, [str(paper_marker_mcp)], root)

    print(f"Install smoke check passed (wheel: {resolved_wheel.name}).")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root (default: parent of scripts/)",
    )
    parser.add_argument("--wheel", type=Path, help="Pre-built wheel; skip build")
    parser.add_argument(
        "--dist-dir",
        type=Path,
        help="Directory containing a built wheel; uses newest *.whl",
    )
    args = parser.parse_args(argv)
    if args.wheel is not None and args.dist_dir is not None:
        parser.error("Use only one of --wheel or --dist-dir")
    run_install_smoke(root=args.root.resolve(), wheel=args.wheel, dist_dir=args.dist_dir)


if __name__ == "__main__":
    main()

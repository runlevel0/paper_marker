# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- **Breaking:** `paper-marker convert` requires `--out-dir`; the implicit default `out/` was removed.
- **Breaking:** MCP `convert_pdf_to_markdown` requires `out_dir`; the implicit default `"out"` was removed.
- Switched issue tracking from the markdown ledger to [GitHub Issues](https://github.com/runlevel0/paper_marker/issues); historical entries archived under `docs/archive/`.

### Added

- MIT `LICENSE` and complete PyPI project metadata (`license`, authors, classifiers, keywords, URLs)
- Contributor documentation (`CONTRIBUTING.md`), environment template (`.env.example`), and this changelog
- Full environment variable reference in README

## [0.1.0] - 2026-06-03

### Added

- Parallel PDF-to-Markdown conversion via external converter CLIs (Marker, MinerU, Nougat, MarkItDown)
- Heuristic candidate scoring and optional OpenRouter/OpenAI-compatible synthesis
- Typer CLI (`paper-marker`) and stdio MCP server (`paper-marker-mcp`)
- GitHub Actions CI and publish workflows
- Fixture catalog integration harness and implementation issues ledger

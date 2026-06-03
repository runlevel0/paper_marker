# Release and Deployment

This project publishes the Python package `paper-marker` to PyPI from Git tags.

## CI and Publish Workflows

- CI workflow: `.github/workflows/ci.yml`
  - Triggers on pull requests and pushes to `main`.
  - Runs `ruff check`, `ruff format --check`, and `pytest -m "not integration"` on Python 3.11 and 3.12.
- Publish workflow: `.github/workflows/publish.yml`
  - Triggers on tags matching `v*.*.*`.
  - Runs quality checks before building and publishing.
  - Publishes with PyPI Trusted Publishing (OIDC), no API token required.

## Required Repository and PyPI Settings

1. In GitHub Actions, ensure the publish job can request OIDC tokens:
   - Workflow/job permissions include `id-token: write`.
2. In PyPI project settings for `paper-marker`, add a trusted publisher:
   - Owner/repository: this GitHub repo.
   - Workflow file: `.github/workflows/publish.yml`.
   - Environment (if used): `pypi`.

## Release Procedure

1. Update `version` in `pyproject.toml`.
2. Merge to `main` after CI passes.
3. Create and push a version tag that matches `pyproject.toml`:

```powershell
git tag vX.Y.Z
git push origin vX.Y.Z
```

4. GitHub Actions runs the publish workflow automatically.
5. Verify the release on [PyPI](https://pypi.org/project/paper-marker/).
6. Review [open GitHub Issues](https://github.com/runlevel0/paper_marker/issues) for blockers or items targeted for the release.

## Safety Guards in Publish Workflow

- Tag/version parity check: `vX.Y.Z` must match `[project].version` in `pyproject.toml`.
- Duplicate publish protection: fails if that version already exists on PyPI.
- Quality gate: lint, formatting, and non-integration tests run before build/publish.
- Concurrency guard: one publish run per tag/ref.

## Rollback and Mitigation

PyPI artifacts cannot be replaced once uploaded.

- If a bad release is published:
  1. Yank the bad version on PyPI.
  2. Fix the issue in `main`.
  3. Bump patch version and publish a new tag.

## Deployment Model

Deployment is package distribution through PyPI. Consumers install either as a CLI tool or as a library dependency.

### Recommended Install Commands

```powershell
uv tool install paper-marker
```

Pin to a specific version for reproducibility:

```powershell
uv tool install "paper-marker==X.Y.Z"
```

### Post-install Smoke Checks

```powershell
paper-marker --help
paper-marker-mcp --help
```

# CLAUDE.md

This file provides guidance to AI agents when working with code in this repository.

## Project Overview

This is an HDX (Humanitarian Data Exchange) scraper that downloads Common Operational Datasets - Administrative Boundaries (COD-AB) from OCHA's ArcGIS server (gis.unocha.org) and publishes them as country datasets to HDX.

## Common Commands

```shell
# Setup environment
uv sync
uv run pre-commit install

# Run the pipeline
python run.py
# Or via taskipy:
uv run task app

# Run tests with coverage
uv run task test
# Run a single test
pytest tests/test_cod_ab.py::TestCODAB::test_cod_ab -v

# Linting and formatting
uv run task ruff
# Pre-commit will also run ruff on commit
```

## Key Design Patterns

- **Retry with Tenacity**: All external HTTP calls wrapped with `@retry` decorator
- **GeoParquet Intermediate**: All data flows through GeoParquet before format conversion
- **Two-tier Metadata**: Maintains both all-versions and latest-version metadata tables
- **Timestamp Skip**: `download_boundaries` fetches ArcGIS metadata XML per layer, parses `CreaDate/Time`, `SyncDate/Time`, `ModDate/Time`, and skips if no layer was modified in the last 1.5 days; pass `--force` to bypass
- **Resource Reuse Detection**: SHA256 comparison of GDB files prevents unnecessary uploads
- **GDAL CLI Processing**: Geometry validation and format conversion handled by GDAL commands

## Code Style

- **Formatter/linter**: `ruff` — run `uv run task ruff` before committing
- **All ruff rules enabled** with a small ignore list (see `pyproject.toml`)
- Config files are consolidated in `pyproject.toml` (no separate `hatch.toml`, `pytest.ini`, or `ruff.toml`)
- Use `uv` for all dependency management — do not use `pip` directly
- Tests live in `tests/` and mirror the module structure (e.g. `test_arcgis.py`, `test_geodata_compare.py`)

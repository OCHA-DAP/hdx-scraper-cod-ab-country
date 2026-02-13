# AGENTS.md

This file provides guidance to AI agents when working with code in this repository.

## Project Overview

This is an HDX (Humanitarian Data Exchange) scraper that downloads Common Operational Datasets - Administrative Boundaries (COD-AB) from OCHA's ArcGIS server (gis.unocha.org) and publishes them as country datasets to HDX.

## Common Commands

```shell
# Setup environment
uv sync
source .venv/bin/activate
pre-commit install

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

## Architecture

### Main Pipeline Flow (`__main__.py`)

1. **Token Generation**: Authenticates with ArcGIS Server via `generate_token()`
2. **Metadata Download**: Downloads global COD metadata table, refactors it into `metadata_all.parquet` (all versions) and `metadata_latest.parquet` (latest per country)
3. **Layer Iteration**: For each country (ISO3 code):
   - Downloads boundary Feature Layers as GeoParquet
   - Converts to multiple formats (GDB, SHP, GeoJSON, XLSX) using GDAL
   - Generates HDX dataset with metadata and resources
   - Compares GDB with existing HDX version to avoid unnecessary uploads
   - Uploads to HDX

### Directory Structure

```
src/hdx/scraper/cod_ab_country/
├── __main__.py              # Entry point, main pipeline
├── config.py                # Configuration/environment variables
├── arcgis.py                # Core utilities (token, HTTP client, metadata access)
├── dataset.py               # HDX dataset generation
├── geodata/
│   ├── compare.py           # GDB comparison to detect changes
│   └── formats.py           # Format conversion (GDB/SHP/GeoJSON/XLSX)
├── download/
│   ├── metadata/
│   │   ├── __init__.py      # Download global metadata
│   │   └── process.py       # Transform metadata table
│   └── boundaries/
│       ├── __init__.py      # Download country boundaries
│       └── process.py       # Normalize boundary data
└── config/
    └── hdx_dataset_static.yaml  # Static HDX metadata (license, etc.)
```

### Key Modules

- **`config.py`**: Centralizes all configuration via environment variables (ArcGIS credentials, retry settings, GDAL options, ISO3 filtering)
- **`arcgis.py`**: HTTP client with retry logic (tenacity), token generation, layer list extraction, metadata retrieval
- **`download/metadata/`**: Downloads global metadata table via ESRIJSON, processes it into two Parquet files (all versions + latest)
- **`download/boundaries/`**: Downloads Feature Layers per country, converts ESRIJSON to normalized GeoParquet
- **`geodata/formats.py`**: Converts GeoParquet to GDB, SHP (zipped), GeoJSON, and XLSX using GDAL CLI
- **`geodata/compare.py`**: SHA256 comparison of GDB files to prevent re-uploading unchanged data
- **`dataset.py`**: Builds HDX Dataset objects with metadata, notes, tags, and file resources

### Data Flow

```
┌─────────────────────────────────────────────────────┐
│         ArcGIS Server (gis.unocha.org)              │
│    COD_Global_Metadata + cod_ab_XXX_vYY services    │
└───────────────────────┬─────────────────────────────┘
                        │ ESRIJSON queries
                        ↓
┌─────────────────────────────────────────────────────┐
│              GDAL Vector Operations                 │
│   (read ESRIJSON, validate geometry, convert)       │
└───────────────────────┬─────────────────────────────┘
                        ↓
              ┌─────────┴─────────┐
              ↓                   ↓
       metadata.parquet    boundaries.parquet
       (all + latest)      (normalized GeoParquet)
              │                   │
              └─────────┬─────────┘
                        ↓
          ┌─────────────────────────────┐
          │  Format Conversion (GDAL)   │
          │  GDB, SHP, GeoJSON, XLSX    │
          └─────────────┬───────────────┘
                        ↓
          ┌─────────────────────────────┐
          │  GDB Compare (vs existing)  │
          └─────────────┬───────────────┘
                        ↓
          ┌─────────────────────────────┐
          │  HDX Dataset Generation     │
          │  + Upload (create_in_hdx)   │
          └─────────────────────────────┘
```

### Key Design Patterns

- **Retry with Tenacity**: All external HTTP calls wrapped with `@retry` decorator
- **GeoParquet Intermediate**: All data flows through GeoParquet before format conversion
- **Two-tier Metadata**: Maintains both all-versions and latest-version metadata tables
- **Resource Reuse Detection**: SHA256 comparison of GDB files prevents unnecessary uploads
- **GDAL CLI Processing**: Geometry validation and format conversion handled by GDAL commands

### Docker

The project uses the UNOCHA base image (`public.ecr.aws/unocha/python:3.13-stable`) which pre-bundles GDAL and other geospatial dependencies. Additional Alpine packages installed at build time:

- `gdal-driver-parquet` + `gdal-tools` (runtime)
- `build-base`, `gdal-dev`, `git`, `python3-dev`, `uv` (build-only, removed after install)

`uv sync --frozen --no-dev --no-editable` installs deps into `/opt/venv`.

### Required Configuration

Environment variables (or `.env` file):

- `ARCGIS_USERNAME`, `ARCGIS_PASSWORD`: ArcGIS authentication
- `ISO3_INCLUDE`, `ISO3_EXCLUDE`: Filter countries to process (optional)

Home directory files:

- `~/.hdx_configuration.yaml`: HDX API key and site config
- `~/.useragents.yaml`: User agent config (key: `hdx-scraper-cod-ab`)

### External Dependencies

- GDAL CLI tools (`gdal`) must be installed and in PATH
- HDX Python libraries (`hdx-python-api`, `hdx-python-country`, `hdx-python-utilities`)

## Code Style

- **Formatter/linter**: `ruff` — run `uv run task ruff` before committing
- **All ruff rules enabled** with a small ignore list (see `pyproject.toml`)
- Config files are consolidated in `pyproject.toml` (no separate `hatch.toml`, `pytest.ini`, or `ruff.toml`)
- Use `uv` for all dependency management — do not use `pip` directly
- Tests live in `tests/` and mirror the module structure (e.g. `test_arcgis.py`, `test_geodata_compare.py`)

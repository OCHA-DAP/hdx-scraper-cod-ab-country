# Collector for COD-AB Datasets

[![Build Status](https://github.com/OCHA-DAP/hdx-scraper-cod-ab/actions/workflows/run-python-tests.yaml/badge.svg)](https://github.com/OCHA-DAP/hdx-scraper-cod-ab/actions/workflows/run-python-tests.yaml)
[![Coverage Status](https://coveralls.io/repos/github/OCHA-DAP/hdx-scraper-cod-ab/badge.svg?branch=main&ts=1)](https://coveralls.io/github/OCHA-DAP/hdx-scraper-cod-ab?branch=main)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

This script ...

## Development

### Environment

Development is currently done using Python 3.13. We recommend using a virtual
environment:

```shell
    uv venv
    source .venv/bin/activate
```

In your virtual environment, install all packages for development by running:

```shell
    uv sync
```

### Installing and running

For the script to run, you will need to have a file called
.hdx_configuration.yaml in your home directory containing your HDX key, e.g.:

    hdx_key: "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
    hdx_read_only: false
    hdx_site: prod

You will also need to supply the universal .useragents.yaml file in your home
directory as specified in the parameter _user_agent_config_yaml_ passed to
facade in run.py. The collector reads the key
**hdx-scraper-cod-ab** as specified in the parameter
_user_agent_lookup_.

Alternatively, you can set up environment variables: `USER_AGENT`, `HDX_KEY`,
`HDX_SITE`, `EXTRA_PARAMS`, `TEMP_DIR`, and `LOG_FILE_ONLY`.

To install and run, execute:

```shell
    python -m hdx.scraper.cod_ab
```

### Pre-commit

Be sure to install `pre-commit`, which is run every time you make a git commit:

```shell
    pre-commit install
```

With pre-commit, all code is formatted according to
[ruff](https://docs.astral.sh/ruff/) guidelines.

To check if your changes pass pre-commit without committing, run:

```shell
    pre-commit run --all-files
```

### Testing

To run the tests and view coverage, execute:

```shell
    pytest --cov hdx
```

## Packages

[uv](https://github.com/astral-sh/uv) is used for package management. If
you’ve introduced a new package to the source code (i.e. anywhere in `src/`),
please add it to the `project.dependencies` section of `pyproject.toml` with
any known version constraints.

To add packages required only for testing, add them to the `dev` section under
`[project.optional-dependencies]`.

Any changes to the dependencies will be automatically reflected in
`requirements.txt` and `requirements-dev.txt` with `pre-commit`, but you can
re-generate the files without committing by executing:

```shell
    pre-commit run --all-files
```

## Project

[Hatch](https://hatch.pypa.io/) is used for project management. The project can be built using:

```shell
    hatch build
```

Linting and syntax checking can be run with:

```shell
    hatch fmt --check
```

Tests can be executed using:

```shell
    hatch test
```

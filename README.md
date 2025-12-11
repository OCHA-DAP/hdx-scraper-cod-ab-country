# Collector for COD-AB Datasets

[![Build Status](https://github.com/OCHA-DAP/hdx-scraper-cod-ab/actions/workflows/run-python-tests.yaml/badge.svg)](https://github.com/OCHA-DAP/hdx-scraper-cod-ab/actions/workflows/run-python-tests.yaml)
[![Coverage Status](https://coveralls.io/repos/github/OCHA-DAP/hdx-scraper-cod-ab/badge.svg?branch=main&ts=1)](https://coveralls.io/github/OCHA-DAP/hdx-scraper-cod-ab?branch=main)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

This script downloads the latest Common Operational Datasets - Administrative Boundaries (COD-AB) from [gis.unocha.org](https://gis.unocha.org/server/rest/services/Hosted) and generates country datasets.

## Development

### Environment

[uv](https://github.com/astral-sh/uv) is used for package management with development done using Python >=3.13. Pre-commit formatting follows [ruff](https://docs.astral.sh/ruff/) guidelines. To get set up:

```shell
    uv sync
    source .venv/bin/activate
    pre-commit install
```

For the script to run, you will need to have a file called `.hdx_configuration.yaml` in your home directory containing your HDX key, e.g.:

```shell
hdx_key: "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
hdx_read_only: false
hdx_site: prod
```

You will also need to supply the universal `.useragents.yaml` file in your home directory as specified in the parameter `user_agent_config_yaml` passed to facade in run.py. The collector reads the key `hdx-scraper-cod-ab-country` as specified in the parameter `user_agent_lookup`.

Alternatively, you can set up environment variables: `USER_AGENT`, `HDX_KEY`, `HDX_SITE`, `EXTRA_PARAMS`, `TEMP_DIR`, and `LOG_FILE_ONLY`.

### Running Pipeline

Execute the pipeline with:

```shell
    python run.py
```

## Configuration

### Environment Variables

This pipeline is configured to access COD-AB data from [gis.unocha.org](https://gis.unocha.org/server/rest/services/Hosted). The `Hosted` folder is the default export location for the ArcGIS Enterprise Server, many other layers are available here aside from COD-AB layers. COD-AB layers are distinguished as those starting with `Hosted/cod_ab_`. They are not visivble by default, and require authentication to access. The following environment variables set the username and password:

```shell
ARCGIS_USERNAME=
ARCGIS_PASSWORD=
```

With these variables set, the pipeline can run. Without any additional parameters, it will download a [metadata table](https://gis.unocha.org/server/rest/services/Hosted/COD_Global_Metadata/FeatureServer/0) and attempt to create a dataset for each row. To limit which rows have datasets created, two additional environment variables are used:

```shell
ISO3_INCLUDE=
ISO3_EXCLUDE=
```

`ISO3_INCLUDE` accepts a list of ISO-3 codes such as `AFG,BFA,CAF`. This is useful if only a small number of locations need to be run. Conversely, if most locations are intended to be run with the exception of a few, it may be easier to pass those to `ISO3_EXCLUDE`.

Both these variables also accept versioned values. For example, if there is an issue with `AFG_v02`, setting `ISO3_INCLUDE=AFG_v01` will force the use of the previous version. This effect can also be achieved by setting `ISO3_EXCLUDE=AFG_v02`. Once `AFG_v03` becomes available, the `INCLUDE` configuration will not run with the new layer, while the `EXCLUDE` configuration will.

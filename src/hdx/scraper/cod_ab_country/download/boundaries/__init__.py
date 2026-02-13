# ruff: noqa: ERA001
from pathlib import Path
from subprocess import run
from urllib.parse import urlencode

from tenacity import retry, stop_after_attempt, wait_fixed

from ...arcgis import client_get
from ...config import ARCGIS_SERVICE_URL, ATTEMPT, OBJECTID, WAIT


def _parse_fields(fields: list) -> tuple[str, str]:
    objectid = next(x["name"] for x in fields if x["type"] == OBJECTID)
    field_names = ",".join(
        [
            x["name"]
            for x in fields
            if x["type"] != OBJECTID
            and not x.get("virtual")
            and not x["name"].lower().startswith("objectid")
        ],
    )
    return objectid, field_names


@retry(stop=stop_after_attempt(ATTEMPT), wait=wait_fixed(WAIT))
def _download_feature(data_dir: Path, url: str, params: dict, response: dict) -> None:
    """Download a ESRIJSON from a Feature Layer."""
    layer_name = response["name"]
    fields = response["fields"]
    objectid, field_names = _parse_fields(fields)
    query = {
        **params,
        "orderByFields": objectid,
        "outFields": field_names,
        "where": "1=1",
    }
    query_url = f"{url}/query?{urlencode(query)}"
    output_file = data_dir / f"{layer_name}.parquet"
    # revert to gdal vector set-field-type once GDAL >= 3.12 is available
    # run(
    #     [
    #         *["gdal", "vector", "set-field-type"],
    #         *["ESRIJSON:" + query_url, output_file],
    #         *["--src-field-type=DateTime", "--dst-field-type=Date"],
    #         *gdal_parquet_options,
    #     ],
    #     check=False,
    # )
    run(
        [
            "ogr2ogr",
            *[output_file, "ESRIJSON:" + query_url],
            *["-mapFieldType", "DateTime=Date"],
            "-overwrite",
            *["-lco", "COMPRESSION=ZSTD"],
        ],
        check=False,
    )


@retry(stop=stop_after_attempt(ATTEMPT), wait=wait_fixed(WAIT))
def download_boundaries(data_dir: Path, token: str, iso3: str, version: str) -> None:
    """Download all ESRIJSON from the URL provided."""
    params = {"f": "json", "token": token}
    url = f"{ARCGIS_SERVICE_URL}/cod_ab_{iso3.lower()}_{version}/FeatureServer"
    response_layers = client_get(url, params).json()
    if "layers" not in response_layers:
        url = url.replace(version, f"v_{version[-2:]}")
        response_layers = client_get(url, params).json()
    for layer in response_layers["layers"]:
        if layer["type"] == "Feature Layer":
            feature_url = f"{url}/{layer['id']}"
            response_feature = client_get(feature_url, params).json()
            _download_feature(data_dir, feature_url, params, response_feature)

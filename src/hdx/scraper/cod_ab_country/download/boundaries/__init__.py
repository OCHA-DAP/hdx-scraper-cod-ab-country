from pathlib import Path
from subprocess import run
from urllib.parse import urlencode

from ...config import ARCGIS_SERVICE_URL
from ...utils import client_get
from ..utils import parse_fields


def download_feature(data_dir: Path, url: str, params: dict, response: dict) -> None:
    """Download a ESRIJSON from a Feature Layer."""
    layer_name = response["name"]
    fields = response["fields"]
    objectid, field_names = parse_fields(fields)
    query = {
        **params,
        "orderByFields": objectid,
        "outFields": field_names,
        "where": "1=1",
    }
    query_url = f"{url}/query?{urlencode(query)}"
    output_file = data_dir / f"{layer_name}.parquet"
    run(
        [
            "ogr2ogr",
            *["-lco", "COMPRESSION=ZSTD"],
            *["-mapFieldType", "DateTime=Date"],
            *[output_file, "ESRIJSON:" + query_url],
        ],
        check=True,
    )


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
            download_feature(data_dir, feature_url, params, response_feature)

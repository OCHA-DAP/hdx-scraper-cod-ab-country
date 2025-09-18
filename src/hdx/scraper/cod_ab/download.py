from pathlib import Path
from subprocess import run
from urllib.parse import urlencode

from pandas import read_parquet, to_datetime

from .config import OBJECTID
from .utils import client_get


def parse_fields(fields: list) -> tuple[str, str]:
    """Extract the OBJECTID and field names from a config."""
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


def download_metadata_table(data_dir: Path, url: str, token: str) -> None:
    """Download the metadata table from a Feature Layer."""
    params = {"f": "json", "token": token}
    fields = client_get(url, params).json()["fields"]
    objectid, field_names = parse_fields(fields)
    query = {
        **params,
        "orderByFields": objectid,
        "outFields": field_names,
        "where": "1=1",
    }
    query_url = f"{url}/query?{urlencode(query)}"
    output_file = data_dir / "metadata.parquet"
    run(
        [
            *["gdal", "vector", "convert"],
            "--overwrite",
            *["ESRIJSON:" + query_url, output_file],
            *["--lco=COMPRESSION=ZSTD"],
        ],
        check=False,
    )
    # TODO (Max): change back to parquet once issue addressed:  # noqa: FIX002
    # https://github.com/OSGeo/gdal/issues/13093
    df = read_parquet(output_file)
    for col in df.columns:
        try:
            if col.startswith("date_"):
                df[col] = to_datetime(df[col], format="ISO8601")
                df[col] = df[col].dt.date
        except ValueError:
            pass
    df.to_parquet(data_dir / "metadata.parquet", compression="zstd")


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
        check=False,
    )


def main(data_dir: Path, url: str, token: str) -> None:
    """Download all ESRIJSON from the URL provided."""
    params = {"f": "json", "token": token}
    response_layers = client_get(url, params).json()
    for layer in response_layers["layers"]:
        if layer["type"] == "Feature Layer":
            feature_url = f"{url}/{layer['id']}"
            response_feature = client_get(feature_url, params).json()
            download_feature(data_dir, feature_url, params, response_feature)


def cleanup(iso3_dir: Path) -> None:
    """Cleanup downloaded files."""
    for src_dataset in sorted(iso3_dir.glob("*.parquet")):
        src_dataset.unlink(missing_ok=True)


def cleanup_metadata(data_dir: Path) -> None:
    """Cleanup downloaded files."""
    output_file = data_dir / "metadata.parquet"
    output_file.unlink(missing_ok=True)

from pathlib import Path
from subprocess import run
from urllib.parse import urlencode

from ...arcgis import client_get
from ...config import ARCGIS_METADATA_URL, OBJECTID
from .process import refactor


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


def download_metadata(data_dir: Path, token: str) -> None:
    """Download the metadata table from a Feature Layer."""
    params = {"f": "json", "token": token}
    fields = client_get(ARCGIS_METADATA_URL, params).json()["fields"]
    objectid, field_names = _parse_fields(fields)
    query = {
        **params,
        "orderByFields": objectid,
        "outFields": field_names,
        "where": "1=1",
    }
    query_url = f"{ARCGIS_METADATA_URL}/query?{urlencode(query)}"
    output_file = data_dir / "metadata/metadata.parquet"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            *["gdal", "vector", "convert"],
            *["ESRIJSON:" + query_url, output_file],
            "--overwrite",
            # "--quiet", ADD THIS BACK IN GDAL 3.12
            "--lco=COMPRESSION_LEVEL=15",
            "--lco=COMPRESSION=ZSTD",
        ],
        check=False,
    )
    refactor(output_file)

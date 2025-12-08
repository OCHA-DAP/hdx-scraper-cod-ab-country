from pathlib import Path
from subprocess import run
from urllib.parse import urlencode

from ...config import ARCGIS_METADATA_URL
from ...utils import client_get
from ..utils import parse_fields
from .refactor import refactor


def download_metadata(data_dir: Path, token: str) -> None:
    """Download the metadata table from a Feature Layer."""
    params = {"f": "json", "token": token}
    fields = client_get(ARCGIS_METADATA_URL, params).json()["fields"]
    objectid, field_names = parse_fields(fields)
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
            "--quiet",
            "--lco=COMPRESSION_LEVEL=15",
            "--lco=COMPRESSION=ZSTD",
        ],
        check=True,
    )
    refactor(output_file)

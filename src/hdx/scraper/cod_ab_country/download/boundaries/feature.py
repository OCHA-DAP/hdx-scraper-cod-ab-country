from pathlib import Path
from subprocess import run
from urllib.parse import urlencode

from tenacity import retry, stop_after_attempt, wait_fixed

from ...config import ATTEMPT, WAIT
from ..utils import parse_fields
from .refactor import refactor


@retry(stop=stop_after_attempt(ATTEMPT), wait=wait_fixed(WAIT))
def download_feature(
    output_dir: Path,
    url: str,
    params: dict,
    response: dict,
    where_query: str = "1=1",
) -> None:
    """Download a ESRIJSON from a Feature Layer."""
    layer_name = response["name"]
    fields = response["fields"]
    objectid, field_names = parse_fields(fields)
    query = {
        **params,
        "orderByFields": objectid,
        "outFields": field_names,
        "where": where_query,
    }
    query_url = f"{url}/query?{urlencode(query)}"
    output_file = output_dir / f"{layer_name}_tmp.parquet"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            *["gdal", "vector", "pipeline", "!"],
            *["read", "ESRIJSON:" + query_url, "!"],
            *["make-valid", "!"],
            *[
                "set-field-type",
                "--src-field-type=DateTime",
                "--dst-field-type=Date",
                "!",
            ],
            *["write", output_file],
            "--overwrite",
            "--quiet",
            "--lco=COMPRESSION_LEVEL=15",
            "--lco=COMPRESSION=ZSTD",
        ],
        check=True,
    )
    refactor(output_file)

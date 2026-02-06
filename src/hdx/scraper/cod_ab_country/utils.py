import logging
from pathlib import Path

from httpx import Client, Response
from pandas import read_parquet
from tenacity import retry, stop_after_attempt, wait_fixed

from .config import (
    ARCGIS_PASSWORD,
    ARCGIS_SERVER,
    ARCGIS_USERNAME,
    ATTEMPT,
    EXPIRATION,
    TIMEOUT,
    WAIT,
    iso3_include_cfg,
)

logger = logging.getLogger(__name__)


@retry(stop=stop_after_attempt(ATTEMPT), wait=wait_fixed(WAIT))
def client_get(url: str, params: dict | None = None) -> Response:
    """HTTP GET with retries, waiting, and longer timeouts."""
    with Client(http2=True, timeout=TIMEOUT) as client:
        return client.get(url, params=params)


def generate_token() -> str:
    """Generate a token for ArcGIS Server."""
    url = f"{ARCGIS_SERVER}/portal/sharing/rest/generateToken"
    data = {
        "username": ARCGIS_USERNAME,
        "password": ARCGIS_PASSWORD,
        "referer": f"{ARCGIS_SERVER}/portal",
        "expiration": EXPIRATION,
        "f": "json",
    }
    with Client(http2=True) as client:
        r = client.post(url, data=data).json()
        return r["token"]


def get_layer_list(data_dir: Path) -> list[tuple[str, str]]:
    """Get a list of ISO3 codes available on the ArcGIS server."""
    layers = read_parquet(
        data_dir / "metadata/metadata_latest.parquet",
        columns=["country_iso3", "version"],
    ).itertuples(index=False, name=None)
    layer_list = []
    for iso3, version in layers:
        if iso3_include_cfg:
            if any(x.startswith(iso3) and x != iso3 for x in iso3_include_cfg):
                version_include = next(
                    x for x in iso3_include_cfg if x.startswith(iso3)
                )
                version_include = version_include.split("_")[1].lower()
                layer_list.append((iso3, version_include))
            elif iso3 in iso3_include_cfg:
                layer_list.append((iso3, version))
        else:
            layer_list.append((iso3, version))
    return layer_list


def get_metadata(data_dir: Path, iso3: str, version: str) -> dict:
    """Get metadata for a country."""
    df = read_parquet(data_dir / "metadata/metadata_all.parquet")
    try:
        df_meta = df[(df["country_iso3"] == iso3) & (df["version"] == version)]
        return df_meta.to_dict("records")[0]
    except IndexError:
        logger.exception("Metadata not found for %s", iso3)
        return {}

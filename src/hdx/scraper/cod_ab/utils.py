import logging
import re
from pathlib import Path

from httpx import Client, Response
from pandas import read_parquet
from tenacity import retry, stop_after_attempt, wait_fixed

from .config import (
    ARCGIS_PASSWORD,
    ARCGIS_SERVER,
    ARCGIS_SERVICE_REGEX,
    ARCGIS_SERVICE_URL,
    ARCGIS_USERNAME,
    ATTEMPT,
    EXPIRATION,
    TIMEOUT,
    WAIT,
    iso3_exclude,
    iso3_include,
)

logger = logging.getLogger(__name__)


@retry(stop=stop_after_attempt(ATTEMPT), wait=wait_fixed(WAIT))
def client_get(url: str, params: dict | None = None) -> Response:
    """HTTP GET with retries, waiting, and longer timeouts."""
    with Client(http2=True, timeout=TIMEOUT) as client:
        return client.get(url, params=params)


def get_metadata(data_dir: Path, iso3: str) -> dict:
    """Get metadata for a country."""
    df = read_parquet(data_dir / "metadata.parquet")
    try:
        return df[
            (df["country_iso3"] == iso3)
            & ((df["version"] == "") | df["version"].isna())
        ].to_dict("records")[0]
    except IndexError:
        logger.exception("Metadata not found for %s", iso3)
        return {}


def get_feature_server_url(iso3: str) -> str:
    """Get a url for a feature server."""
    return f"{ARCGIS_SERVICE_URL}/cod_ab_{iso3.lower()}/FeatureServer"


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


def get_iso3_list(token: str) -> list[str]:
    """Get a list of ISO3 codes available on the ArcGIS server."""
    params = {"f": "json", "token": token}
    services = client_get(ARCGIS_SERVICE_URL, params=params).json()["services"]
    p = re.compile(ARCGIS_SERVICE_REGEX)
    iso3_list = [
        x["name"][14:17].upper()
        for x in services
        if x["type"] == "FeatureServer" and p.search(x["name"])
    ]
    return [
        iso3
        for iso3 in iso3_list
        if (not iso3_include or iso3 in iso3_include)
        and (not iso3_exclude or iso3 not in iso3_exclude)
    ]

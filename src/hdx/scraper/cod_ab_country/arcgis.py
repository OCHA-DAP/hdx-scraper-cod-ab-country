import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from xml.etree.ElementTree import ParseError

from defusedxml.ElementTree import fromstring
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

_DATE_LEN = 8
_CUTOFF_DAYS = 1.5
_DATE_TIME_PAIRS = [
    ("CreaDate", "CreaTime"),
    ("SyncDate", "SyncTime"),
    ("ModDate", "ModTime"),
]


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


def _parse_date_time(date_str: str, time_str: str) -> datetime | None:
    """Parse a YYYYMMDD + HHMMSSxx string pair into a UTC datetime."""
    try:
        return datetime(
            int(date_str[0:4]),
            int(date_str[4:6]),
            int(date_str[6:8]),
            int(time_str[0:2]),
            int(time_str[2:4]),
            int(time_str[4:6]),
            tzinfo=UTC,
        )
    except ValueError:
        return None


def parse_metadata_datetimes(
    url: str, params: dict, service_url: str
) -> list[datetime]:
    """Fetch layer metadata XML and return all UTC datetimes found."""
    response = client_get(f"{url}/metadata", params)
    try:
        root = fromstring(response.text)
    except ParseError:
        logger.warning("Failed to parse metadata XML from %s/metadata", url)
        response = client_get(f"{service_url}/info/metadata", params)
        try:
            root = fromstring(response.text)
        except ParseError:
            logger.warning(
                "Failed to parse metadata XML from %s/info/metadata", service_url
            )
            return []
    datetimes = []
    esri = root.find("Esri")
    if esri is not None:
        for date_tag, time_tag in _DATE_TIME_PAIRS:
            date_el = esri.find(date_tag)
            time_el = esri.find(time_tag)
            if date_el is not None and date_el.text and len(date_el.text) == _DATE_LEN:
                time_str = (
                    (time_el.text or "").ljust(_DATE_LEN, "0")
                    if time_el is not None
                    else "00000000"
                )
                dt = _parse_date_time(date_el.text, time_str)
                if dt is not None:
                    datetimes.append(dt)
    return datetimes


def is_recently_updated(url: str, params: dict, service_url: str) -> bool:
    """Return True if any metadata datetime is within the last 1.5 days."""
    cutoff_utc = datetime.now(UTC) - timedelta(days=_CUTOFF_DAYS)
    return any(
        dt > cutoff_utc for dt in parse_metadata_datetimes(url, params, service_url)
    )

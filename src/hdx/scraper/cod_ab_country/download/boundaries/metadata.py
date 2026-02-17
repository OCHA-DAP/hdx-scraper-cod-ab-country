import logging
from datetime import UTC, datetime
from xml.etree.ElementTree import ParseError

from defusedxml.ElementTree import fromstring

from ...arcgis import client_get

logger = logging.getLogger(__name__)

_DATE_LEN = 8
_DATE_TIME_PAIRS = [
    ("CreaDate", "CreaTime"),
    ("SyncDate", "SyncTime"),
    ("ModDate", "ModTime"),
]


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

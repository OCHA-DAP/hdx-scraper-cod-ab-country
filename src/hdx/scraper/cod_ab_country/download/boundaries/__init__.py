import logging
from pathlib import Path

from tenacity import retry, stop_after_attempt, wait_fixed

from ...arcgis import client_get, is_recently_updated
from ...config import ARCGIS_SERVICE_URL, ATTEMPT, WAIT
from .download import download_feature

logger = logging.getLogger(__name__)


@retry(stop=stop_after_attempt(ATTEMPT), wait=wait_fixed(WAIT))
def download_boundaries(
    data_dir: Path,
    token: str,
    iso3: str,
    version: str,
    force: bool = False,  # noqa: FBT001, FBT002
) -> None:
    """Download all ESRIJSON from the URL provided."""
    params = {"f": "json", "token": token}
    url = f"{ARCGIS_SERVICE_URL}/cod_ab_{iso3.lower()}_{version}/FeatureServer"
    response_layers = client_get(url, params).json()
    if "layers" not in response_layers:
        url = url.replace(version, f"v_{version[-2:]}")
        response_layers = client_get(url, params).json()
    feature_layers = [
        layer for layer in response_layers["layers"] if layer["type"] == "Feature Layer"
    ]
    if not force:
        any_modified = any(
            is_recently_updated(f"{url}/{layer['id']}", params, url)
            for layer in feature_layers
        )
        if not any_modified:
            logger.info(
                "Skipping %s %s: no layers modified in the last 1.5 days", iso3, version
            )
            return
    for layer in feature_layers:
        feature_url = f"{url}/{layer['id']}"
        response_feature = client_get(feature_url, params).json()
        download_feature(data_dir, feature_url, params, response_feature)

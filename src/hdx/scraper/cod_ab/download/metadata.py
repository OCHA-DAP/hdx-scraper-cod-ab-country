import re

from hdx.utilities.retriever import Retrieve

from hdx.scraper.cod_ab.config import services_url
from hdx.scraper.cod_ab.utils import generate_token

p1 = re.compile(r"[a-z]{3}_admin\d$")
p2 = re.compile(r"[a-z]{3}_adminlines$")
p3 = re.compile(r"[a-z]{3}_admincentroids$")


def polygons(iso3: str, retriever: Retrieve) -> list[int]:
    """Get the layer index from the ArcGIS server."""
    params = {"f": "json", "token": generate_token()}
    service_name = f"cod_{iso3.lower()}_ab_standardized"
    layers_url = f"{services_url}/{service_name}/FeatureServer"
    layers = retriever.download_json(layers_url, parameters=params)["layers"]
    return [
        x["id"] for x in sorted(layers, key=lambda x: x["name"]) if p1.search(x["name"])
    ]


def lines(iso3: str, retriever: Retrieve) -> list[int]:
    """Get the layer index from the ArcGIS server."""
    params = {"f": "json", "token": generate_token()}
    service_name = f"cod_{iso3.lower()}_ab_standardized"
    layers_url = f"{services_url}/{service_name}/FeatureServer"
    layers = retriever.download_json(layers_url, parameters=params)["layers"]
    return [
        x["id"] for x in sorted(layers, key=lambda x: x["name"]) if p2.search(x["name"])
    ]


def points(iso3: str, retriever: Retrieve) -> list[int]:
    """Get the layer index from the ArcGIS server."""
    params = {"f": "json", "token": generate_token()}
    service_name = f"cod_{iso3.lower()}_ab_standardized"
    layers_url = f"{services_url}/{service_name}/FeatureServer"
    layers = retriever.download_json(layers_url, parameters=params)["layers"]
    return [
        x["id"] for x in sorted(layers, key=lambda x: x["name"]) if p3.search(x["name"])
    ]

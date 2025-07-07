from pathlib import Path

from hdx.utilities.retriever import Retrieve

from . import metadata, ogr2ogr, points, postprocess
from hdx.scraper.cod_ab.config import services_url


def download_polygons(iso3: str, retriever: Retrieve, data_dir: Path) -> None:
    """Download polygons from ArcGIS server."""
    points_path = data_dir / iso3.lower() / f"{iso3.lower()}_adminpoints.parquet"
    points_path.unlink(missing_ok=True)
    indexes = metadata.polygons(iso3, retriever)
    for lvl, index in enumerate(indexes):
        url = f"{services_url}/cod_{iso3.lower()}_ab_standardized/FeatureServer/{index}"
        file_path = data_dir / iso3.lower() / f"{iso3.lower()}_admin{lvl}"
        ogr2ogr.main(file_path, url, 3)
        postprocess.to_parquet(file_path)
        points.to_points(file_path)


def download_lines(iso3: str, retriever: Retrieve, data_dir: Path) -> None:
    """Download lines from ArcGIS server."""
    indexes = metadata.lines(iso3, retriever)
    for index in indexes:
        url = f"{services_url}/cod_{iso3.lower()}_ab_standardized/FeatureServer/{index}"
        file_path = data_dir / iso3.lower() / f"{iso3.lower()}_adminlines"
        ogr2ogr.main(file_path, url, 2)
        postprocess.to_parquet(file_path)


def download_points(iso3: str, retriever: Retrieve, data_dir: Path) -> None:
    """Download points from ArcGIS server."""
    indexes = metadata.points(iso3, retriever)
    for index in indexes:
        url = f"{services_url}/cod_{iso3.lower()}_ab_standardized/FeatureServer/{index}"
        file_path = data_dir / iso3.lower() / f"{iso3.lower()}_adminpoints"
        ogr2ogr.main(file_path, url, 1)
        postprocess.to_parquet(file_path)


def main(iso3: str, retriever: Retrieve, data_dir: Path) -> None:
    """Entrypoint for the module."""
    download_polygons(iso3, retriever, data_dir)
    download_lines(iso3, retriever, data_dir)
    download_points(iso3, retriever, data_dir)

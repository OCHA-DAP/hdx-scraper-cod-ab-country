# flake8: noqa: E501

import logging
from pathlib import Path

from hdx.data.dataset import Dataset
from hdx.data.organization import Organization
from hdx.data.resource import Resource
from hdx.location.country import Country

logger = logging.getLogger(__name__)

format_types = [
    ("gdb.zip", "Geodatabase"),
    ("geojson.zip", "GeoJSON"),
    ("shp.zip", "zipped shapefile"),
    ("xlsx", "XLSX"),
]


def get_notes(iso3: str, metadata: dict) -> str:
    """Compile notes for a dataset."""
    country_name = Country.get_country_name_from_iso3(iso3)
    admin_level = metadata["admin_level_max"]
    admin_level_range = "0" if admin_level == 0 else f"0-{admin_level}"
    year_established = metadata["date_source"].strftime("%Y")
    date_reviewed = metadata["date_reviewed"].strftime("%B %Y")
    source = metadata["source"]
    requires_update = "The COD-AB does not require any updates."
    if metadata.get("cod_ab_requires_improvement"):
        requires_update = "The COD-AB requires improvements."
    ps_dataset = "There is no suitable population statistics dataset (COD-PS) for linkage to this COD-AB."
    if metadata.get("cod_ps_available"):
        ps_dataset = f"This COD-AB is suitable for database or GIS linkage to the {country_name} population statistics ([COD-PS](https://data.humdata.org/dataset/cod-ps-{iso3.lower()})) dataset."
    em_dataset = (
        "No edge-matched (COD-EM) version of this COD-AB has yet been prepared."
    )
    if metadata.get("cod_em_available"):
        em_dataset = f"An edge-matched (COD-EM) version of this COD-AB is available on HDX [here](https://data.humdata.org/dataset/cod-em-{iso3.lower()})."
    features_info = []
    for level in range(1, admin_level + 1):
        count = metadata[f"admin_{level}_count"]
        feature_type = metadata[f"admin_{level}_name"]
        features_info.append(
            f"Administrative level {level} contains {count} feature(s). The normal administrative level {level} feature type is '{feature_type}'.",
        )
    lines = [
        f"{country_name} administrative level {admin_level_range} boundaries (COD-AB) dataset.",
        f"These administrative boundaries were established in {year_established}.",
        f"This COD-AB was most recently reviewed for accuracy and necessary changes in {date_reviewed}. {requires_update}",
        f"Sourced from {source}.",
        ps_dataset,
        em_dataset,
    ]
    lines = lines + features_info
    return "  \n  \n".join(lines)


def initialize_dataset(iso3: str) -> Dataset | None:
    """Initialize a dataset."""
    country_name = Country.get_country_name_from_iso3(iso3)
    if not country_name:
        logger.error("Country not found for %s", iso3)
        return None
    dataset_name = f"cod-ab-{iso3.lower()}"
    dataset_title = f"{country_name} - Subnational Administrative Boundaries"
    dataset = Dataset({"name": dataset_name, "title": dataset_title})
    dataset.add_country_location(iso3)
    dataset.add_tags(["administrative boundaries-divisions", "gazetteer"])
    dataset["cod_level"] = "cod-enhanced"
    return dataset


def add_metadata(iso3: str, metadata: dict, dataset: Dataset) -> Dataset | None:
    """Add metadata to a dataset."""
    if not metadata:
        logger.error("No metadata for %s", iso3)
        return None

    dataset_time_start = metadata.get("date_valid_from")
    dataset_time_end = metadata.get("date_reviewed")
    if not dataset_time_start or not dataset_time_end:
        logger.error("Dates not present for %s", iso3)
        return None
    dataset.set_time_period(
        dataset_time_start.isoformat(),
        dataset_time_end.isoformat(),
    )

    org_name = metadata["contributor"]
    org = Organization.autocomplete(org_name)
    if len(org) != 1:
        logger.error("Matching organization not found for %s", org_name)
        return None
    dataset.set_organization(org[0])

    dataset["dataset_source"] = metadata["source"]
    dataset["caveats"] = metadata["caveates"]

    return dataset


def add_resources(
    iso3_dir: Path,
    iso3: str,
    metadata: dict,
    dataset: Dataset,
) -> Dataset:
    """Add resources to a dataset."""
    admin_level = metadata["admin_level_max"]
    country_name = Country.get_country_name_from_iso3(iso3)
    admin_level_range = "0" if admin_level == 0 else f"0-{admin_level}"
    for ext, format_type in format_types:
        resource_name = f"{iso3.lower()}_admin_boundaries.{ext}"
        resource_desc = (
            f"{country_name} administrative level {admin_level_range} {format_type}"
        )
        if format_type == "XLSX":
            resource_desc = resource_desc.replace("XLSX", "gazetteer")
        resource_data = {
            "name": resource_name,
            "description": resource_desc,
        }
        if admin_level > 0:
            resource_data["p_coded"] = True
        resource = Resource(resource_data)
        resource.set_file_to_upload(str(iso3_dir / resource_name))
        resource.set_format(format_type)
        dataset.add_update_resource(resource)
        if format_type == "Shapefile":
            resource.enable_dataset_preview()

    dataset.preview_resource()
    return dataset


def generate_dataset(iso3_dir: Path, iso3: str, metadata: dict) -> Dataset | None:
    """Generate a dataset for a country."""
    dataset = initialize_dataset(iso3)
    if not dataset:
        return None
    dataset = add_metadata(iso3, metadata, dataset)
    if not dataset:
        return None
    dataset["notes"] = get_notes(iso3, metadata)
    return add_resources(iso3_dir, iso3, metadata, dataset)

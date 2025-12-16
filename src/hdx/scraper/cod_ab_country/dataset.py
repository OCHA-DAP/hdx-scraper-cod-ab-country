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
    ("shp.zip", "SHP"),
    ("geojson.zip", "GeoJSON"),
    ("xlsx", "XLSX"),
]


def initialize_dataset(iso3: str) -> Dataset | None:
    """Initialize a dataset."""
    country_name = Country.get_country_name_from_iso3(iso3)
    if not country_name:
        logger.error("Country not found for %s", iso3)
        return None
    dataset_title = f"{country_name} - Subnational Administrative Boundaries"
    return Dataset({"name": f"cod-ab-{iso3.lower()}", "title": dataset_title})


def add_metadata(iso3: str, metadata: dict, dataset: Dataset) -> Dataset | None:
    """Add metadata to a dataset."""
    dataset_time_start = metadata["date_valid_on"]
    dataset_time_end = metadata["date_reviewed"] or dataset_time_start
    if not dataset_time_start or not dataset_time_end:
        logger.error("Dates not present for %s", iso3)
        return None
    dataset_time_end = max(dataset_time_end, dataset_time_start)
    dataset.set_time_period(
        dataset_time_start.isoformat(),
        dataset_time_end.isoformat(),
    )
    dataset["data_update_frequency"] = metadata["update_frequency"] * 365
    dataset.add_country_location(iso3)
    dataset["dataset_source"] = metadata["source"]
    org_name = metadata["contributor"]
    org = Organization.autocomplete(org_name)
    if len(org) not in (1, 2):
        logger.error("Matching organization not found for '%s'", org_name)
        return None
    dataset.set_organization(org[0])
    methodology_dataset = metadata["methodology_dataset"]
    methodology_pcodes = metadata["methodology_pcodes"]
    methodology = [
        f"Dataset: {methodology_dataset}" if methodology_dataset else None,
        f"P-codes: {methodology_pcodes}" if methodology_pcodes else None,
    ]
    methodology = [x for x in methodology if x]
    dataset["methodology_other"] = "  \n  \n".join(methodology)
    dataset["caveats"] = metadata["caveats"] or None
    dataset.add_tags(["administrative boundaries-divisions", "gazetteer", "geodata"])
    return dataset


def get_notes(iso3: str, metadata: dict) -> str:
    """Compile notes for a dataset."""
    country_name = Country.get_country_name_from_iso3(iso3)
    admin_levels = metadata["admin_level_max"]
    admin_level_range = "0" if admin_levels == 0 else f"0-{admin_levels}"
    levels_plural = "s" if admin_levels != 1 else ""
    lines = [
        f"{country_name} administrative level {admin_level_range} boundaries (COD-AB) dataset version {metadata['version'][1:]}.",
        "",
        f"This dataset is structured into {admin_levels} level{levels_plural}:",
    ]
    for level in range(1, admin_levels + 1):
        admin_units = metadata[f"admin_{level}_count"] or ""
        admin_type = metadata[f"admin_{level}_name"] or ""
        admin_partial = (
            level > metadata["admin_level_full"]
            if metadata["admin_level_full"] != "Unknown"
            else False
        )
        partial_text = ", partial coverage" if admin_partial else ""
        lines.append(
            f"- Admin {level}: {admin_units} {admin_type}{partial_text}",
        )
    admin_notes = metadata["admin_notes"]
    if admin_notes:
        lines.extend(["", "", f"Note: {admin_notes}"])
    lines.extend(["", "", "Dates associated with this dataset:"])
    date_format = "%d %B %Y"
    dates = [
        f"- {metadata['date_reviewed'].strftime(date_format)}: dataset reviewed for accuracy and completeness"
        if metadata["date_reviewed"]
        else None,
        f"- {metadata['date_valid_on'].strftime(date_format)}: valid for use by the humanitarian community"
        if metadata["date_valid_on"]
        else None,
        f"- {metadata['date_updated'].strftime(date_format)}: last edit to the dataset before publishing"
        if metadata["date_updated"]
        else None,
        f"- {metadata['date_source'].strftime(date_format)}: boundaries created by the source"
        if metadata["date_source"]
        else None,
    ]
    dates = [x for x in dates if x]
    lines.extend(dates)
    vetting = [
        "",
        "Quality assured, configured, and published by HDX and OCHA Field Information Services (FIS).",
        "",
        "Part of the dataset: [Global Subnational Administrative Boundaries](https://data.humdata.org/dataset/cod-ab-global)",
    ]
    lines.extend(vetting)
    return "  \n".join(lines)


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
        resource_desc = f"{country_name} administrative level {admin_level_range} boundaries (COD-AB), {format_type}"
        resource_data = {"name": resource_name, "description": resource_desc}
        if admin_level > 0:
            resource_data["p_coded"] = "True"
        resource = Resource(resource_data)
        resource.set_file_to_upload(str(iso3_dir / resource_name))
        resource.set_format(format_type)
        dataset.add_update_resource(resource)
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

#!/usr/bin/python
"""cod_ab scraper."""

import logging
from datetime import datetime
from pathlib import Path

from hdx.data.dataset import Dataset
from hdx.data.organization import Organization
from hdx.data.resource import Resource
from hdx.location.country import Country
from hdx.utilities.dateparse import parse_date
from pandas import read_excel

logger = logging.getLogger(__name__)


def generate_dataset(
    metadata: dict, iso3: str, data_dir: Path, today: datetime
) -> Dataset | None:
    if not metadata.get("all"):
        logger.error(f"No metadata for {iso3}")
        return None
    country_name = Country.get_country_name_from_iso3(iso3)
    if not country_name:
        logger.error(f"Country not found for {iso3}")
        return None
    dataset_name = f"cod-ab-{iso3.lower()}"
    dataset_title = f"{country_name} - Subnational Administrative Boundaries"
    dataset = Dataset(
        {
            "name": dataset_name,
            "title": dataset_title,
        },
    )

    dataset_time_start = metadata["all"].get("date_established")
    dataset_time_end = metadata["all"].get("date_reviewed")
    if not dataset_time_start or not dataset_time_end:
        logger.error(f"Dates not present for {iso3}")
        return None
    dataset.set_time_period(dataset_time_start, dataset_time_end)

    dataset_tags = ["administrative boundaries-divisions", "gazetteer"]
    dataset.add_tags(dataset_tags)

    dataset.add_country_location(iso3)

    orig_org = metadata["all"]["contributor"]
    org = Organization.autocomplete(orig_org)
    if len(org) != 1:
        logger.error(f"Matching organization not found for {orig_org}")
        return None
    dataset.set_organization(org[0])

    dataset["dataset_source"] = metadata["all"]["source"]
    dataset["caveats"] = ""  # TODO: fill in caveats if needed

    feature_counts = get_feature_counts(
        data_dir / iso3.lower() / f"{iso3.lower()}_cod_ab.xlsx"
    )
    admin_level = metadata["all"]["level_deepest"]
    expected_keys = [f"adm{level}" for level in range(0, admin_level + 1)]
    if sorted(list(feature_counts.keys())) != expected_keys:
        logger.error(f"Not all admin levels found for {iso3}")
        return None

    dataset["notes"] = compile_notes(
        iso3, country_name, metadata, feature_counts, today
    )

    cod_level = "cod-standard"
    enhanced = metadata["all"].get("cod_ab_quality_checked")
    if enhanced:
        cod_level = "cod-enhanced"
    dataset["cod_level"] = cod_level

    # Add resources
    if admin_level == 0:
        admin_level_range = "0"
    else:
        admin_level_range = f"0-{admin_level}"
    for ext, format_type in [
        ("xlsx", "XLSX"),
        ("shp.zip", "zipped shapefile"),
        ("geojson.zip", "GeoJSON"),
        ("gdb.zip", "Geodatabase"),
    ]:
        resource_name = f"{iso3.lower()}_cod_ab.{ext}"
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
        resource.set_file_to_upload(data_dir / iso3.lower() / resource_name)
        resource.set_format(format_type)
        dataset.add_update_resource(resource)
        if format_type == "Shapefile":
            resource.enable_dataset_preview()

    dataset.preview_resource()
    return dataset


def get_feature_counts(file_path: str) -> dict[str, int]:
    feature_counts = {}
    gazetteer = read_excel(file_path, sheet_name=None)
    for sheet_name, contents in gazetteer.items():
        if "lines" in sheet_name:
            continue
        admin_level = sheet_name[-1]
        feature_count = len(contents)
        feature_counts[f"adm{admin_level}"] = feature_count
    return feature_counts


def compile_notes(
    iso3: str, country_name: str, metadata: dict, feature_counts: dict, today: datetime
) -> str:
    admin_level = metadata["all"]["level_deepest"]
    if admin_level == 0:
        admin_level_range = "0"
    else:
        admin_level_range = f"0-{admin_level}"
    year_established = metadata["all"]["date_established"][:4]
    date_reviewed = parse_date(metadata["all"]["date_reviewed"])
    date_reviewed = date_reviewed.strftime("%B %Y")
    source = metadata["all"]["source"]
    requires_update = "The COD-AB does not require any updates."
    if metadata["all"].get("cod_ab_requires_improvement"):
        requires_update = "The COD-AB requires improvements."
    ps_dataset = "There is no suitable population statistics dataset (COD-PS) for linkage to this COD-AB."
    if metadata["all"].get("cod_ps_available"):
        ps_dataset = f"This COD-AB is suitable for database or GIS linkage to the {country_name} population statistics ([COD-PS](https://data.humdata.org/dataset/cod-ps-{iso3.lower()})) dataset."
    em_dataset = (
        "No edge-matched (COD-EM) version of this COD-AB has yet been prepared."
    )
    if metadata["all"].get("cod_em_available"):
        em_dataset = f"An edge-matched (COD-EM) version of this COD-AB is available on HDX [here](https://data.humdata.org/dataset/cod-em-{iso3.lower()})."
    features_info = []
    for level in range(1, admin_level + 1):
        count = feature_counts[f"adm{level}"]
        feature_type = metadata[f"adm{level}"]["feature_type"]
        features_info.append(
            f"Administrative level {level} contains {count} feature(s). The normal administrative level {level} feature type is '{feature_type}'."
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
    notes = "  \n  \n".join(lines)
    return notes

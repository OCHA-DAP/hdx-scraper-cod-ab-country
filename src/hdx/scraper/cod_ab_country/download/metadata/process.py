"""Metadata table refactoring and enrichment."""

from pathlib import Path

from pandas import read_parquet

from hdx.scraper.cod_ab_country.config import (
    admin_level_full_overrides,
    iso3_exclude_cfg,
)

ISO3_LEN = 3

count_columns = [
    "admin_1_count",
    "admin_2_count",
    "admin_3_count",
    "admin_4_count",
    "admin_5_count",
]

columns = [
    "country_name",
    "country_iso2",
    "country_iso3",
    "version",
    "admin_level_full",
    "admin_level_max",
    "admin_1_name",
    "admin_2_name",
    "admin_3_name",
    "admin_4_name",
    "admin_5_name",
    "admin_1_count",
    "admin_2_count",
    "admin_3_count",
    "admin_4_count",
    "admin_5_count",
    "admin_notes",
    "date_source",
    "date_updated",
    "date_reviewed",
    "date_metadata",
    "date_valid_on",
    "date_valid_to",
    "update_frequency",
    "update_type",
    "source",
    "contributor",
    "methodology_dataset",
    "methodology_pcodes",
    "caveats",
]


def refactor(output_file: Path) -> None:
    """Refactor file."""
    iso3_exclude_all = [x for x in iso3_exclude_cfg if len(x) == ISO3_LEN]
    iso3_exclude_version = [x.replace("_V", "v") for x in iso3_exclude_cfg if "_V" in x]
    df = read_parquet(output_file)
    df["country_name"] = df["country_name"].str.replace("\u2019", "'", regex=False)
    df["admin_level_full"] = df["admin_level_full"].astype("Int32")
    for iso3, level in admin_level_full_overrides.items():
        df.loc[df["country_iso3"] == iso3, "admin_level_full"] = level
    df[count_columns] = df[count_columns].astype("Int32")
    df = df[~df["country_iso3"].isin(iso3_exclude_all)]
    df = df[~(df["country_iso3"] + df["version"]).isin(iso3_exclude_version)]
    df = df[columns].sort_values(by=["country_iso3", "version"])
    df.to_parquet(
        output_file.parent / "metadata_all.parquet",
        compression="zstd",
        compression_level=15,
        index=False,
    )
    df = df.drop_duplicates(subset=["country_iso3"], keep="last")
    df.to_parquet(
        output_file.parent / "metadata_latest.parquet",
        compression="zstd",
        compression_level=15,
        index=False,
    )

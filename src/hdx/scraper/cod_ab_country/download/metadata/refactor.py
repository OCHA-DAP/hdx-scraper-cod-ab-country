from pathlib import Path

from hdx.location.country import Country
from pandas import read_parquet

from ...config import iso3_exclude

ISO3_LEN = 3

column_rename = {
    "date_valid_from": "date_valid_on",
    "caveates": "caveats",
}

contributor_updates = {
    "IRQ": "OCHA Middle East and North Africa (ROMENA)",
}

name_columns = [
    "admin_1_name",
    "admin_2_name",
    "admin_3_name",
    "admin_4_name",
    "admin_5_name",
]

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
    iso3_exclude_all = [x for x in iso3_exclude if len(x) == ISO3_LEN]
    iso3_exclude_version = [x.replace("_V", "v") for x in iso3_exclude if "_V" in x]
    df = read_parquet(output_file)
    df = df.rename(columns=column_rename)
    for key, value in contributor_updates.items():
        df.loc[df["country_iso3"] == key, "contributor"] = value
    df["country_name"] = df["country_iso3"].apply(Country.get_country_name_from_iso3)
    df["country_iso2"] = df["country_iso3"].apply(Country.get_iso2_from_iso3)
    df[name_columns] = df[name_columns].replace("currently not known", None)
    df["admin_level_full"] = df["admin_level_full"].replace("Unknown", None)
    df["admin_level_full"] = df["admin_level_full"].fillna(
        df["admin_level_max"].astype("string"),
    )
    df["admin_level_full"] = df["admin_level_full"].astype("Int32")
    df[count_columns] = df[count_columns].astype("Int32")
    df = df[df["version"] != ""]
    df = df[df["admin_level_max"].gt(0)]
    df = df[~df["country_iso3"].isin(iso3_exclude_all)]
    df = df[~(df["country_iso3"] + df["version"]).isin(iso3_exclude_version)]
    df = df[columns].sort_values(by=["country_iso3", "version"])
    df.to_parquet(
        output_file.with_stem(output_file.stem + "_all"),
        compression="zstd",
        compression_level=15,
        index=False,
    )
    df = df.drop_duplicates(subset=["country_iso3"], keep="last")
    df.to_parquet(
        output_file.with_stem(output_file.stem + "_latest"),
        compression="zstd",
        compression_level=15,
        index=False,
    )
    output_file.unlink()

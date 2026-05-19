# flake8: noqa: E501
"""Metadata table refactoring and enrichment."""

from pathlib import Path

from hdx.location.country import Country
from pandas import read_parquet, to_numeric

from hdx.scraper.cod_ab_country.config import iso3_exclude_cfg

ISO3_LEN = 3

column_rename = {
    "date_valid_from": "date_valid_on",
    "caveates": "caveats",
}

source_updates = {
    "GEO": "National Statistics Office of Georgia [Administraciuli erTeulebi]",
    "GTM": "Coordinadora Nacional Para La Reducción De Desastres",
    "HND": "Sistema Nacional de Información Territorial (SINIT), Secretaria Técnica de Planificación y Cooperación Externa (SEPLAN), 2010",
    "IDN": "Badan Pusat Statistik (BPS - Statistics Indonesia)",
    "IRN": "UNHCR",
    "IRQ": "Iraq Central Statistics Office",
    "JAM": "Jamaica Social Development Commission (sdc.gov.jm)",
    "KGZ": "Ministry of Emergency Situations of the Kyrgyz Republic",
    "LBY": "UNITAR-UNOSAT, Libyan Bureau of Statistics, WFP, and Global Logistics Cluster, International Organisation for Migration (IOM)",
    "MEX": "Instituto Nacional de Estadística y Geografía (INEGI)",
    "MWI": "National Statistics Office of Malawi",
    "PER": "Instituto Geográfico Nacional - IGN",
    "PHL": "National Mapping and Resource Information Authority (NAMRIA), Philippines Statistics Authority (PSA)",
    "PRK": "World Food Programme",
    "SLV": "www.gadm.org",
    "ZWE": "Zimbabwe National Statistics Agency (ZIMSTAT www.zimstat.co.zw) Central Statistics Office",
}

contributor_updates = {
    "BFA": "OCHA Burkina Faso",
    "GEO": "OCHA Middle East and North Africa (ROMENA)",
    "GTM": "OCHA Field Information Services Section (FISS)",
    "HND": "OCHA Latin America and the Caribbean (ROLAC)",
    "IDN": "OCHA Regional Office for Asia and the Pacific (ROAP)",
    "IRN": "OCHA Middle East and North Africa (ROMENA)",
    "IRQ": "OCHA Middle East and North Africa (ROMENA)",
    "JAM": "OCHA Field Information Services Section (FISS)",
    "KGZ": "OCHA Middle East and North Africa (ROMENA)",
    "LBY": "OCHA Middle East and North Africa (ROMENA)",
    "MEX": "OCHA Latin America and the Caribbean (ROLAC)",
    "MWI": "OCHA Field Information Services Section (FISS)",
    "PER": "OCHA Latin America and the Caribbean (ROLAC)",
    "PHL": "OCHA Philippines",
    "PRK": "OCHA Regional Office for Asia and the Pacific (ROAP)",
    "SLV": "OCHA Field Information Services Section (FISS)",
    "ZWE": "OCHA Regional Office for Southern and Eastern Africa (ROSEA)",
}

admin_level_full_updates = [
    ("COD", "v01", 3),
    ("KGZ", "v01", 1),
    ("PHL", "v03", 3),
    ("QAT", "v01", 1),
    ("QAT", "v02", 1),
]

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
    iso3_exclude_all = [x for x in iso3_exclude_cfg if len(x) == ISO3_LEN]
    iso3_exclude_version = [x.replace("_V", "v") for x in iso3_exclude_cfg if "_V" in x]
    df = read_parquet(output_file)
    df = df.rename(columns=column_rename)
    for key, value in source_updates.items():
        df.loc[df["country_iso3"] == key, "source"] = value
    for key, value in contributor_updates.items():
        df.loc[df["country_iso3"] == key, "contributor"] = value
    df["country_name"] = df["country_iso3"].apply(Country.get_country_name_from_iso3)
    df["country_iso2"] = df["country_iso3"].apply(Country.get_iso2_from_iso3)
    df[name_columns] = df[name_columns].replace("currently not known", None)
    df["admin_level_full"] = to_numeric(df["admin_level_full"], errors="coerce").fillna(
        to_numeric(df["admin_level_max"], errors="coerce")
    )
    df["admin_level_full"] = df["admin_level_full"].astype("Int32")
    for iso3, version, level in admin_level_full_updates:
        df.loc[
            (df["country_iso3"] == iso3) & (df["version"] == version),
            "admin_level_full",
        ] = level
    df[count_columns] = df[count_columns].replace("", None).astype("Int32")
    df["admin_level_max"] = df["admin_level_max"].astype("int32")
    df["update_frequency"] = df["update_frequency"].astype("int32")
    df = df[df["version"] != ""]
    df = df[df["admin_level_max"].gt(0)]
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

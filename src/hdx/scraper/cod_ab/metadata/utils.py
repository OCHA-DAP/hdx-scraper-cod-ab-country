from datetime import UTC, datetime
from re import sub
from typing import Any

import numpy as np
from hdx.utilities.retriever import Retrieve
from pandas import read_csv

from hdx.scraper.cod_ab.metadata import config


def get_meta(retriever: Retrieve, iso3: str = "") -> list[dict]:
    """Gets metadata from google sheets.

    Args:
        retriever (Retrieve): Retriever object.
        iso3: iso3 value to filter by

    Returns:
        input list of data
    """
    csv_path = retriever.download_file(
        config.metadata_url, filename=f"{iso3.lower()}_dynamic_ab_metadata.csv"
    )
    meta_list = read_csv(csv_path, na_values=config.na_values)
    if iso3:
        meta_list = meta_list[meta_list[config.ISO3] == iso3.upper()]
    return meta_list[config.meta_long_columns].to_dict("records")


def process_key(key: str) -> str:
    """Normalizes a key into all lowercase with underscores."""
    key = str(key).replace(" ", "_").replace("-", "_").lower()
    return config.rename_columns.get(key, key)


def process_string(value: str) -> str:
    """Normalizes a string by removing special quotes and extra spaces."""
    for char in config.apostrophe_chars:
        value = value.replace(chr(int(char[2:], 16)), "'")
    for char in config.quote_chars:
        value = value.replace(chr(int(char[2:], 16)), '"')
    for char in config.invisible_chars:
        value = value.replace(chr(int(char[2:], 16)), "")
    value = sub(r" +", " ", value)
    return value.strip()


def process_value(key: str, value: Any) -> str | int | bool:  # noqa: ANN401
    """Normalizes values based on multiple conditions."""
    if isinstance(value, str):
        value = process_string(value)
    if value.lower() in ["true", "false"]:
        value = value.lower() == "true"
    elif "currently not known" in value.lower():
        value = None
    elif key in config.integer_columns:
        value = "".join(filter(str.isdigit, value))
        value = None if value == "" else int(value)
    elif key.startswith("date_"):
        if "unknown" in value.lower():
            value = None
        else:
            value = datetime.strptime(value, "%B %Y").astimezone(UTC).date().isoformat()
    elif key == "cod_ab_requires_improvement":
        value = "improvement" in value.lower()
    elif key == "cod_ab_quality_checked":
        value = "enhanced" in value.lower()
    elif key == "ocha_operational_country":
        value = "operational" in value.lower()
    elif key in ["cod_em_available", "cod_ps_available"]:
        value = bool(value)
    return value


def process_long(meta_list: list) -> list[dict]:
    """Cleans data in long format.

    Args:
        meta_list: input list of data

    Returns:
        cleaned data
    """
    meta_long = []
    for row in meta_list:
        if np.nan in [
            row[config.ISO3],
            row[config.LVL],
            row[config.KEY],
            row[config.VALUE],
        ]:
            continue
        iso3 = row[config.ISO3]
        lvl = int(row[config.LVL])
        key = process_key(row[config.KEY])
        if key in config.ignored_columns:
            continue
        value = process_value(key, row[config.VALUE])
        meta_long.append({"iso3": iso3, "lvl": lvl, "key": key, "value": value})
    return sorted(meta_long, key=lambda x: (x["iso3"], x["lvl"], x["key"]))


def process_dict(meta_long: list, iso3_val: str) -> dict:
    """Nests values by key for use in JSON and YAML.

    Args:
        meta_long: cleaned data in long form
        iso3_val: iso3 value to filter by

    Returns:
        Data nested by keys
    """
    meta_dict = {}
    for row in meta_long:
        iso3, lvl, key, value = row.values()
        iso3 = iso3.lower()
        lvl = "all" if lvl == -1 else f"adm{lvl}"
        meta_dict[iso3] = meta_dict.get(iso3, {})
        meta_dict[iso3][lvl] = meta_dict[iso3].get(lvl, {})
        if key in meta_dict[iso3][lvl]:
            if isinstance(meta_dict[iso3][lvl][key], list):
                meta_dict[iso3][lvl][key].append(value)
            else:
                meta_dict[iso3][lvl][key] = [meta_dict[iso3][lvl][key], value]
        else:
            meta_dict[iso3][lvl][key] = value
    if iso3_val:
        return meta_dict.get(iso3_val.lower(), {})
    return meta_dict

import json
from pathlib import Path

from hdx.utilities.retriever import Retrieve
from pandas import DataFrame

from hdx.scraper.cod_ab.metadata.utils import get_meta, process_dict, process_long


def main(iso3: str, retriever: Retrieve, data_dir: Path) -> dict:
    """Downloads metadata from google sheet."""
    meta_list = get_meta(retriever, iso3)
    meta_long = process_long(meta_list)
    meta_dict = process_dict(meta_long, iso3)
    json_path = data_dir / iso3.lower() / f"{iso3.lower()}_metadata.json"
    json_path.write_text(json.dumps(meta_dict))
    csv_path = data_dir / iso3.lower() / f"{iso3.lower()}_metadata.csv"
    DataFrame(meta_long).to_csv(csv_path, encoding="utf-8-sig", index=False)
    return meta_dict

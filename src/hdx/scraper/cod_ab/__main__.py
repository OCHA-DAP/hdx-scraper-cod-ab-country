#!/usr/bin/python
"""Top level script.

Calls other functions that generate datasets that this script then creates in HDX.
"""

import logging
from os.path import dirname, expanduser, join
from pathlib import Path
from shutil import rmtree

from hdx.api.configuration import Configuration
from hdx.facades.infer_arguments import facade
from hdx.utilities.dateparse import now_utc
from hdx.utilities.downloader import Download
from hdx.utilities.path import wheretostart_tempdir_batch
from hdx.utilities.retriever import Retrieve
from tqdm import tqdm

from hdx.scraper.cod_ab import checks, download, formats, metadata, scores
from hdx.scraper.cod_ab.cod_ab import generate_dataset
from hdx.scraper.cod_ab.config import DEBUG
from hdx.scraper.cod_ab.utils import get_iso3_list

logger = logging.getLogger(__name__)

_USER_AGENT_LOOKUP = "hdx-scraper-cod-ab"
_SAVED_DATA_DIR = "saved_data"  # Keep in repo to avoid deletion in /tmp
_UPDATED_BY_SCRIPT = "HDX Scraper: COD-AB"


def main(
    save: bool = True,
    use_saved: bool = False,
) -> None:
    """Generate datasets and create them in HDX.
    Args:
        save (bool): Save downloaded data. Defaults to True.
        use_saved (bool): Use saved data. Defaults to False.

    Returns:
        None
    """
    Configuration.read()
    today = now_utc()
    with wheretostart_tempdir_batch(folder=_USER_AGENT_LOOKUP) as info:
        temp_dir = info["folder"]
        with Download(rate_limit={"calls": 5, "period": 10}, timeout=60) as downloader:
            retriever = Retrieve(
                downloader=downloader,
                fallback_dir=temp_dir,
                saved_dir=_SAVED_DATA_DIR,
                temp_dir=temp_dir,
                save=save,
                use_saved=use_saved,
            )
            data_dir = _SAVED_DATA_DIR if save or use_saved else temp_dir
            data_dir = Path(data_dir)
            iso3_list = get_iso3_list(retriever)
            pbar = tqdm(iso3_list)
            for iso3 in pbar:
                pbar.set_postfix_str(iso3)
                iso3_dir = data_dir / iso3.lower()
                if not DEBUG or (DEBUG and not iso3_dir.exists()):
                    iso3_dir.mkdir(exist_ok=True, parents=True)
                    download.main(iso3, retriever, data_dir)
                    formats.main(iso3, data_dir)
                    checks.main(iso3, data_dir)
                score = scores.main(iso3, data_dir)
                logger.info(f"{iso3} Score: {score}")
                meta_dict = metadata.main(iso3, retriever, data_dir)
                dataset = generate_dataset(meta_dict, iso3, data_dir, today)
                if not dataset:
                    continue
                dataset.update_from_yaml(
                    path=join(dirname(__file__), "config", "hdx_dataset_static.yaml"),
                )
                dataset.create_in_hdx(
                    remove_additional_resources=True,
                    match_resource_order=False,
                    hxl_update=False,
                    updated_by_script=_UPDATED_BY_SCRIPT,
                    batch=info["batch"],
                )
                if not DEBUG:
                    rmtree(iso3_dir, ignore_errors=True)


if __name__ == "__main__":
    facade(
        main,
        hdx_site="dev",
        user_agent_config_yaml=join(expanduser("~"), ".useragents.yaml"),
        user_agent_lookup=_USER_AGENT_LOOKUP,
    )

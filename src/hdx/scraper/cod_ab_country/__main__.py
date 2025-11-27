import logging
from pathlib import Path
from shutil import rmtree

from hdx.api.configuration import Configuration
from hdx.facades.infer_arguments import facade
from hdx.utilities.path import wheretostart_tempdir_batch
from tqdm import tqdm

from . import formats
from .dataset import generate_dataset
from .download.boundaries import download_boundaries
from .download.metadata import download_metadata
from .utils import generate_token, get_layer_list, get_metadata

logger = logging.getLogger(__name__)
cwd = Path(__file__).parent

_USER_AGENT_LOOKUP = "hdx-scraper-cod-ab"
_SAVED_DATA_DIR = (cwd / "../../../../saved_data").resolve()
_UPDATED_BY_SCRIPT = "HDX Scraper: COD-AB Country"


def create_country_dataset(
    info: dict,
    data_dir: Path,
    token: str,
    iso3: str,
    version: str,
) -> None:
    """Create a dataset for a country."""
    iso3_dir = data_dir / "boundaries" / iso3.lower()
    rmtree(iso3_dir, ignore_errors=True)
    iso3_dir.mkdir(parents=True)
    download_boundaries(iso3_dir, token, iso3, version)
    formats.main(iso3_dir, iso3)
    metadata = get_metadata(data_dir, iso3, version)
    dataset = generate_dataset(iso3_dir, iso3, metadata)
    if dataset:
        dataset.update_from_yaml(path=str(cwd / "config/hdx_dataset_static.yaml"))
        dataset.create_in_hdx(
            remove_additional_resources=True,
            match_resource_order=False,
            hxl_update=False,
            updated_by_script=_UPDATED_BY_SCRIPT,
            batch=info["batch"],
        )
    rmtree(iso3_dir)


def main(save: bool = True, use_saved: bool = False) -> None:  # noqa: FBT001, FBT002
    """Generate datasets and create them in HDX."""
    Configuration.read()
    with wheretostart_tempdir_batch(folder=_USER_AGENT_LOOKUP) as info:
        temp_dir = info["folder"]
        data_dir = Path(_SAVED_DATA_DIR if save or use_saved else temp_dir)
        data_dir.mkdir(parents=True, exist_ok=True)
        token = generate_token()
        download_metadata(data_dir, token)
        layer_list = get_layer_list(data_dir)
        pbar = tqdm(layer_list)
        for iso3, version in pbar:
            pbar.set_postfix_str(iso3)
            create_country_dataset(info, data_dir, token, iso3, version)
        rmtree(data_dir)


if __name__ == "__main__":
    facade(
        main,
        user_agent_config_yaml=str(Path("~").expanduser() / ".useragents.yaml"),
        user_agent_lookup=_USER_AGENT_LOOKUP,
    )

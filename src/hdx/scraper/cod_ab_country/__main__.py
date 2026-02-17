from pathlib import Path
from shutil import rmtree

from hdx.api.configuration import Configuration
from hdx.facades.infer_arguments import facade
from hdx.utilities.path import wheretostart_tempdir_batch
from tqdm import tqdm

from .arcgis import generate_token, get_layer_list, get_metadata
from .config import TEMP_DIR, iso3_exclude_cfg, iso3_include_cfg
from .dataset import generate_dataset
from .download.boundaries import download_boundaries
from .download.metadata import download_metadata
from .geodata import formats

cwd = Path(__file__).parent

_USER_AGENT_LOOKUP = "hdx-scraper-cod-ab"
_SAVED_DATA_DIR = f"{TEMP_DIR}/saved_data"
_UPDATED_BY_SCRIPT = "HDX Scraper: COD-AB Country"


def _create_country_dataset(  # noqa: PLR0913
    info: dict,
    data_dir: Path,
    token: str,
    iso3: str,
    version: str,
    force: bool = False,  # noqa: FBT001, FBT002
) -> None:
    """Create a dataset for a country."""
    iso3_dir = data_dir / "boundaries" / iso3.lower()
    rmtree(iso3_dir, ignore_errors=True)
    iso3_dir.mkdir(parents=True)
    download_boundaries(iso3_dir, token, iso3, version, force=force)
    if not any(iso3_dir.glob("*.parquet")):
        rmtree(iso3_dir)
        return
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


def main(
    iso3_include: str = "",
    iso3_exclude: str = "",
    save: bool = True,  # noqa: FBT001, FBT002
    use_saved: bool = False,  # noqa: FBT001, FBT002
    force: bool = False,  # noqa: FBT001, FBT002
) -> None:
    """Generate datasets and create them in HDX."""
    Configuration.read()
    if iso3_include:
        iso3_include_cfg.clear()
        iso3_include_cfg.extend(
            [x.strip() for x in iso3_include.upper().split(",") if x.strip()],
        )
    if iso3_exclude:
        iso3_exclude_cfg.clear()
        iso3_exclude_cfg.extend(
            [x.strip() for x in iso3_exclude.upper().split(",") if x.strip()],
        )
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
            _create_country_dataset(info, data_dir, token, iso3, version, force=force)
        rmtree(data_dir)


if __name__ == "__main__":
    facade(
        main,
        user_agent_config_yaml=str(Path("~").expanduser() / ".useragents.yaml"),
        user_agent_lookup=_USER_AGENT_LOOKUP,
    )

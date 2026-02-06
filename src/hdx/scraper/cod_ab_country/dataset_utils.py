from filecmp import cmpfiles, dircmp
from pathlib import Path
from subprocess import run

from geopandas import list_layers
from hdx.data.dataset import Dataset
from tenacity import retry, stop_after_attempt, wait_fixed

from .config import ATTEMPT, WAIT


@retry(stop=stop_after_attempt(ATTEMPT), wait=wait_fixed(WAIT))
def _download_geodata_from_hdx(
    resource_name: str,
    dataset_name: str,
    download_dir: Path,
) -> Path | None:
    """Download existing zipped geodata from HDX dataset."""
    dataset = Dataset.read_from_hdx(dataset_name)
    if not dataset:
        return None
    for resource in dataset.get_resources():
        if resource["name"] == resource_name:
            _, local_path = resource.download(download_dir)
            return local_path.rename(local_path.with_suffix(""))
    return None


def _convert_geodata(input_path: Path, output_dir: Path, var: str) -> Path:
    """Convert Geodata to GeoPackage using GDAL."""
    layers = list_layers(input_path)["name"]
    var_path = output_dir / f"{input_path.stem}_{var}"
    var_path.mkdir(exist_ok=True, parents=True)
    for layer in layers:
        run(
            [
                *["gdal", "vector", "convert"],
                *[input_path, var_path / f"{layer}.geojson"],
                *["--layer", layer],
                "--quiet",
                "--overwrite",
            ],
            check=False,
        )
    return var_path


def _is_file_same(a: Path, b: Path) -> bool:
    """Compare two files."""
    tmp_dir = b.parent
    a = _convert_geodata(a, tmp_dir, "a")
    b = _convert_geodata(b, tmp_dir, "b")
    _, mismatch, errors = cmpfiles(a, b, dircmp(a, b).common_files, shallow=False)
    return mismatch == [] and errors == []


def compare_geodata(local_path: Path, dataset_name: str) -> Path:
    """Compare local and remote geodata.

    Return local path if files are different,
    otherwise return remote path if they are the same.
    """
    tmp_dir = local_path.parent / "tmp"
    tmp_dir.mkdir(exist_ok=True)
    remote_path = _download_geodata_from_hdx(local_path.name, dataset_name, tmp_dir)
    if not remote_path:
        return local_path
    return remote_path if _is_file_same(local_path, remote_path) else local_path

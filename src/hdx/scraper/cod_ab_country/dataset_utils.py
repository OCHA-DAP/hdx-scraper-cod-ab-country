import hashlib
from pathlib import Path
from subprocess import run

from hdx.data.dataset import Dataset
from tenacity import retry, stop_after_attempt, wait_fixed

from .config import ATTEMPT, WAIT


@retry(stop=stop_after_attempt(ATTEMPT), wait=wait_fixed(WAIT))
def _download_gdb_from_hdx(
    resource_name: str,
    dataset_name: str,
    download_dir: Path,
) -> Path | None:
    """Download existing .gdb.zip from HDX dataset."""
    dataset = Dataset.read_from_hdx(dataset_name)
    if not dataset:
        return None
    for resource in dataset.get_resources():
        if resource["name"] == resource_name:
            _, local_path = resource.download(download_dir)
            return local_path.rename(local_path.with_suffix(""))
    return None


def _convert_gdb_to_gpkg(gdb_path: Path, gpkg_path: Path) -> Path:
    """Convert FileGDB to GeoPackage using GDAL."""
    run(
        [
            *["gdal", "vector", "convert"],
            *[gdb_path, gpkg_path],
            "--quiet",
            "--overwrite",
            *["--config", "OGR_CURRENT_DATE=2000-01-01T00:00:00.000Z"],
        ],
        check=True,
    )
    return gpkg_path


def _is_file_same(a: Path, b: Path) -> bool:
    """Compare two files."""
    tmp_dir = b.parent
    a_gpkg = _convert_gdb_to_gpkg(a, tmp_dir / "a.gpkg")
    b_gpkg = _convert_gdb_to_gpkg(b, tmp_dir / "b.gpkg")
    file_a = hashlib.sha256(a_gpkg.open("rb").read()).digest()
    file_b = hashlib.sha256(b_gpkg.open("rb").read()).digest()
    return file_a == file_b


def compare_gdb(local_gdb_path: Path, dataset_name: str) -> Path:
    """Compare local and remote GDB.

    Return remote path if files are different,
    otherwise return local path if they are the same.
    """
    tmp_dir = local_gdb_path.parent / "tmp"
    tmp_dir.mkdir(exist_ok=True)
    remote_gdb_path = _download_gdb_from_hdx(local_gdb_path.name, dataset_name, tmp_dir)
    if not remote_gdb_path:
        return local_gdb_path
    return (
        remote_gdb_path
        if _is_file_same(local_gdb_path, remote_gdb_path)
        else local_gdb_path
    )

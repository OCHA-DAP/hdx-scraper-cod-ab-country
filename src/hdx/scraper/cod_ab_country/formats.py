from pathlib import Path
from shutil import make_archive, rmtree
from subprocess import run


def get_layer_create_options(suffix: str) -> list[str]:
    """Get layer creation options based on the file suffix."""
    match suffix:
        case ".gdb":
            return ["--lco=TARGET_ARCGIS_VERSION=ARCGIS_PRO_3_2_OR_LATER"]
        case ".shp":
            return ["--lco=ENCODING=UTF-8"]
        case _:
            return []


def get_dst_dataset(src_dataset: Path, dst_dataset: Path, *, multi: bool) -> Path:
    """Return the correct destination path based on file type or multi format."""
    if not multi:
        return dst_dataset / (src_dataset.stem + dst_dataset.suffix)
    if dst_dataset.suffix == ".gdb":
        return dst_dataset / dst_dataset.name
    return dst_dataset


def to_multilayer(src_dataset: Path, dst_dataset: Path, *, multi: bool) -> None:
    """Use GDAL to turn a GeoParquet into a generic layer."""
    lco = get_layer_create_options(dst_dataset.suffixes[0])
    output_options = [f"--nln={src_dataset.stem}"] if multi else []
    dst_dataset = get_dst_dataset(src_dataset, dst_dataset, multi=multi)
    dst_dataset.parent.mkdir(parents=True, exist_ok=True)
    mode = "--append" if dst_dataset.exists() else "--overwrite"
    run(
        [
            *["gdal", "vector", "convert"],
            "--quiet",
            *[src_dataset, dst_dataset],
            mode,
            *lco,
            *output_options,
        ],
        check=True,
    )


def main(iso3_dir: Path, iso3: str) -> None:
    """Convert geometries into multiple formats."""
    for ext, multi in [
        ("gdb", True),
        ("shp.zip", True),
        ("geojson", False),
        ("xlsx", True),
    ]:
        for src_dataset in sorted(iso3_dir.glob("*.parquet")):
            dst_dataset = iso3_dir / f"{iso3.lower()}_admin_boundaries.{ext}"
            to_multilayer(src_dataset, dst_dataset, multi=multi)
        if dst_dataset.is_dir():
            make_archive(str(dst_dataset), "zip", dst_dataset)
            rmtree(dst_dataset)

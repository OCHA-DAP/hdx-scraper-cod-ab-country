"""Geospatial format conversion via GDAL."""

import zipfile
from pathlib import Path
from shutil import make_archive, rmtree
from subprocess import run

import pandas as pd


def _get_layer_create_options(suffix: str) -> list[str]:
    """Get layer creation options based on the file suffix."""
    match suffix:
        case ".gdb":
            return ["--lco=TARGET_ARCGIS_VERSION=ARCGIS_PRO_3_2_OR_LATER"]
        case ".shp":
            return ["--lco=ENCODING=UTF-8"]
        case _:
            return []


def _get_dst_dataset(src_dataset: Path, dst_dataset: Path, *, multi: bool) -> Path:
    """Return the correct destination path based on file type or multi format."""
    if not multi:
        return dst_dataset / (src_dataset.stem + dst_dataset.suffix)
    if dst_dataset.suffix == ".gdb":
        return dst_dataset / dst_dataset.name
    return dst_dataset


def _to_multilayer(src_dataset: Path, dst_dataset: Path, *, multi: bool) -> None:
    """Use GDAL to turn a GeoParquet into a generic layer."""
    lco = _get_layer_create_options(dst_dataset.suffixes[0])
    output_options = [f"--nln={src_dataset.stem}"] if multi else []
    dst_dataset = _get_dst_dataset(src_dataset, dst_dataset, multi=multi)
    dst_dataset.parent.mkdir(parents=True, exist_ok=True)
    mode = "--append" if dst_dataset.exists() else "--overwrite"
    run(
        [
            *["gdal", "vector", "convert"],
            # "--quiet", ADD THIS BACK IN GDAL 3.12
            *[src_dataset, dst_dataset],
            mode,
            *lco,
            *output_options,
        ],
        check=False,
    )


def _table_to_csv(src: Path, dst: Path) -> None:
    pd.read_parquet(src).to_csv(dst, index=False)


def main(iso3_dir: Path, iso3: str) -> None:
    """Convert geometries into multiple formats."""
    tables_dir = iso3_dir / "tables"
    table_files = sorted(tables_dir.glob("*.parquet")) if tables_dir.exists() else []
    for ext, multi in [
        ("gdb", True),
        ("shp.zip", True),
        ("geojson", False),
        ("xlsx", True),
    ]:
        dst_dataset = iso3_dir / f"{iso3.lower()}_admin_boundaries.{ext}"
        for src_dataset in sorted(iso3_dir.glob("*.parquet")):
            _to_multilayer(src_dataset, dst_dataset, multi=multi)
        for table in table_files:
            if ext in ("gdb", "xlsx"):
                _to_multilayer(table, dst_dataset, multi=True)
            elif ext == "shp.zip":
                csv_path = tables_dir / (table.stem + ".csv")
                _table_to_csv(table, csv_path)
                with zipfile.ZipFile(dst_dataset, "a") as zf:
                    zf.write(csv_path, arcname=csv_path.name)
            elif ext == "geojson":
                geojson_dir = dst_dataset
                csv_path = geojson_dir / (table.stem + ".csv")
                _table_to_csv(table, csv_path)
        if dst_dataset.is_dir():
            make_archive(str(dst_dataset), "zip", dst_dataset)
            rmtree(dst_dataset)

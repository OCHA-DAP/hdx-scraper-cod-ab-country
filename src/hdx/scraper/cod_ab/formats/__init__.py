from pathlib import Path
from shutil import rmtree
from subprocess import run


def to_multilayer(src_dataset: Path, dst_dataset: Path, *, multi: bool) -> None:
    """Uses OGR2OGR to turn a GeoParquet into a generic layer."""
    if dst_dataset.suffixes[0] == ".shp":
        lco = ["-lco", "ENCODING=UTF-8"]
    elif dst_dataset.suffix == ".gdb":
        lco = [
            "-lco",
            "TARGET_ARCGIS_VERSION=ARCGIS_PRO_3_2_OR_LATER",
            "-f",
            "OpenFileGDB",
        ]
    else:
        lco = []
    if multi:
        output_options = ["-nln", src_dataset.stem]
    else:
        dst_dataset.mkdir(exist_ok=True, parents=True)
        dst_dataset = (dst_dataset / src_dataset.stem).with_suffix(dst_dataset.suffix)
        output_options = []
    run(
        [
            "ogr2ogr",
            "-overwrite",
            *lco,
            *output_options,
            dst_dataset,
            src_dataset,
        ],
        check=False,
    )


def main(iso3: str, data_dir: Path) -> None:
    """Convert geometries into multiple formats."""
    for ext, multi in [
        ("gdb", True),
        ("shp.zip", True),
        ("geojson", False),
        ("xlsx", True),
    ]:
        for level in [*range(6), "lines"]:
            src_dataset = (
                data_dir / iso3.lower() / f"{iso3.lower()}_admin{level}.parquet"
            )
            dst_dataset = data_dir / iso3.lower() / f"{iso3.lower()}_cod_ab.{ext}"
            if src_dataset.exists():
                to_multilayer(src_dataset, dst_dataset, multi=multi)
        if dst_dataset.is_dir():
            zip_file = dst_dataset.with_suffix(dst_dataset.suffix + ".zip")
            zip_file.unlink(missing_ok=True)
            run(
                [
                    "sozip",
                    "--quiet",
                    "--recurse-paths",
                    "--junk-paths",
                    zip_file,
                    dst_dataset,
                ],
                check=False,
            )
            rmtree(dst_dataset, ignore_errors=True)

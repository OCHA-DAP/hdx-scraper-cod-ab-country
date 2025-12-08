from pathlib import Path
from subprocess import run

from geopandas import read_parquet
from hdx.location.country import Country


def get_columns(admin_level: int, *, only_nullable: bool = False) -> list[str]:
    """Get a list of column names for the given admin level."""
    columns = []
    for level in range(admin_level, -1, -1):
        columns += [f"adm{level}_name"]
        columns += [f"adm{level}_name1", f"adm{level}_name2", f"adm{level}_name3"]
        columns += [f"adm{level}_pcode"]
    columns += ["lang", "lang1", "lang2", "lang3"]
    if only_nullable:
        return columns
    columns += ["iso2", "iso3", "version", "valid_on", "valid_to", "geometry"]
    return columns


def refactor(output_tmp: Path) -> None:
    """Refactor file."""
    output_file = output_tmp.with_stem(output_tmp.stem.replace("_tmp", ""))
    admin_level = int(output_file.stem[-1])
    iso3 = output_file.stem[0:3].upper()
    all_columns = get_columns(admin_level)
    nullable_columns = get_columns(admin_level, only_nullable=True)
    pcode_columns = [f"adm{x}_pcode" for x in range(admin_level, -1, -1)]
    gdf = read_parquet(output_tmp)
    gdf = gdf.rename(columns={"cod_version": "version"}, errors="ignore")
    gdf["iso2"] = Country.get_iso2_from_iso3(iso3)
    gdf["iso3"] = iso3
    gdf["version"] = gdf["version"].str.replace("V_", "v")
    gdf["valid_to"] = gdf["valid_to"].astype("date32[pyarrow]")
    gdf[nullable_columns] = gdf[nullable_columns].astype("string")
    gdf = gdf[all_columns]
    gdf = gdf.sort_values(by=pcode_columns).reset_index()
    gdf.to_parquet(
        output_tmp,
        compression_level=15,
        compression="zstd",
        schema_version="1.1.0",
        write_covering_bbox=True,
        index=False,
    )
    run(
        [
            *["gdal", "vector", "convert"],
            *[output_tmp, output_file],
            "--overwrite",
            "--quiet",
            "--lco=COMPRESSION_LEVEL=15",
            "--lco=COMPRESSION=ZSTD",
        ],
        check=True,
    )
    output_tmp.unlink()

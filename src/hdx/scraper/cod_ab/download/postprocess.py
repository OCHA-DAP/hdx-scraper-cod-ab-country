from pathlib import Path

from geopandas import GeoDataFrame, read_file
from hdx.location.country import Country
from pandas import to_datetime


def add_iso_codes(gdf: GeoDataFrame, file_path: Path) -> GeoDataFrame:
    """Adds ISO codes to a GeoDataFrame based on filename."""
    iso3 = file_path.stem[0:3].upper()
    gdf["iso3"] = iso3
    gdf["iso2"] = Country.get_iso2_from_iso3(iso3)
    return gdf


def to_parquet(file_path: Path) -> None:
    """Uses OGR2OGR to turn a FlatGeobuf into GeoParquet.

    Args:
        file_path: Name of the downloaded layer.
    """
    src_dataset = file_path.with_suffix(".fgb")
    dst_dataset = file_path.with_suffix(".parquet")
    dst_dataset.unlink(missing_ok=True)
    gdf = read_file(src_dataset).convert_dtypes()
    for column in gdf.select_dtypes(include="object").columns:
        if gdf[column].isna().all():
            gdf[column] = gdf[column].astype("string")
        else:
            gdf[column] = gdf[column].astype("int32")
    for column in gdf.select_dtypes(include="datetime64").columns:
        gdf[column] = to_datetime(gdf[column]).astype("date32[pyarrow]")
    for column in [
        "OBJECTID",
        "objectid",
        "SHAPE__Area",
        "Shape__Area",
        "SHAPE__Length",
        "Shape__Length",
    ]:
        if column in gdf.columns:
            gdf = gdf.drop(columns=column)
    for column in [f"adm{lvl}_ref_name" for lvl in range(6)]:
        if column in gdf.columns:
            gdf = gdf.rename(columns={column: column[:-5]})
    gdf = add_iso_codes(gdf, file_path)
    gdf.to_parquet(
        dst_dataset,
        compression="zstd",
        geometry_encoding="geoarrow",
        write_covering_bbox=True,
    )
    src_dataset.unlink(missing_ok=True)

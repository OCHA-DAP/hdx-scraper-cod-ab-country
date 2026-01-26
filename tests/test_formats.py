# flake8: noqa: S101
# ruff: noqa: D102
"""Tests for formats module."""

from pathlib import Path
from unittest.mock import patch

from hdx.scraper.cod_ab_country.formats import (
    get_dst_dataset,
    get_layer_create_options,
    to_multilayer,
)


class TestGetLayerCreateOptions:
    """Tests for get_layer_create_options function."""

    def test_gdb_returns_arcgis_version_option(self) -> None:
        result = get_layer_create_options(".gdb")
        assert result == ["--lco=TARGET_ARCGIS_VERSION=ARCGIS_PRO_3_2_OR_LATER"]

    def test_shp_returns_encoding_option(self) -> None:
        result = get_layer_create_options(".shp")
        assert result == ["--lco=ENCODING=UTF-8"]

    def test_geojson_returns_empty_list(self) -> None:
        result = get_layer_create_options(".geojson")
        assert result == []

    def test_xlsx_returns_empty_list(self) -> None:
        result = get_layer_create_options(".xlsx")
        assert result == []

    def test_unknown_suffix_returns_empty_list(self) -> None:
        result = get_layer_create_options(".unknown")
        assert result == []


class TestGetDstDataset:
    """Tests for get_dst_dataset function."""

    def test_single_layer_format(self, tmp_path: Path) -> None:
        src = tmp_path / "adm1.parquet"
        dst = tmp_path / "output.geojson"
        result = get_dst_dataset(src, dst, multi=False)
        assert result == tmp_path / "output.geojson" / "adm1.geojson"

    def test_multi_layer_gdb(self, tmp_path: Path) -> None:
        src = tmp_path / "adm1.parquet"
        dst = tmp_path / "output.gdb"
        result = get_dst_dataset(src, dst, multi=True)
        assert result == tmp_path / "output.gdb" / "output.gdb"

    def test_multi_layer_shp(self, tmp_path: Path) -> None:
        src = tmp_path / "adm1.parquet"
        dst = tmp_path / "output.shp.zip"
        result = get_dst_dataset(src, dst, multi=True)
        assert result == tmp_path / "output.shp.zip"

    def test_multi_layer_xlsx(self, tmp_path: Path) -> None:
        src = tmp_path / "adm1.parquet"
        dst = tmp_path / "output.xlsx"
        result = get_dst_dataset(src, dst, multi=True)
        assert result == tmp_path / "output.xlsx"


class TestToMultilayer:
    """Tests for to_multilayer function."""

    def test_creates_parent_directory(self, tmp_path: Path) -> None:
        src = tmp_path / "adm1.parquet"
        dst = tmp_path / "subdir" / "output.geojson"

        with patch("hdx.scraper.cod_ab_country.formats.run"):
            to_multilayer(src, dst, multi=False)
            assert dst.parent.exists()

    def test_calls_gdal_with_overwrite_for_new_file(self, tmp_path: Path) -> None:
        src = tmp_path / "adm1.parquet"
        dst = tmp_path / "output.geojson"

        with patch("hdx.scraper.cod_ab_country.formats.run") as mock_run:
            to_multilayer(src, dst, multi=False)

            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "--overwrite" in call_args
            assert "--append" not in call_args

    def test_calls_gdal_with_append_for_existing_file(self, tmp_path: Path) -> None:
        src = tmp_path / "adm1.parquet"
        dst = tmp_path / "output.xlsx"
        dst.touch()

        with patch("hdx.scraper.cod_ab_country.formats.run") as mock_run:
            to_multilayer(src, dst, multi=True)

            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "--append" in call_args
            assert "--overwrite" not in call_args

    def test_includes_layer_name_for_multi(self, tmp_path: Path) -> None:
        src = tmp_path / "adm1.parquet"
        dst = tmp_path / "output.xlsx"

        with patch("hdx.scraper.cod_ab_country.formats.run") as mock_run:
            to_multilayer(src, dst, multi=True)

            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "--nln=adm1" in call_args

    def test_excludes_layer_name_for_single(self, tmp_path: Path) -> None:
        src = tmp_path / "adm1.parquet"
        dst = tmp_path / "output.geojson"

        with patch("hdx.scraper.cod_ab_country.formats.run") as mock_run:
            to_multilayer(src, dst, multi=False)

            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert not any("--nln" in str(arg) for arg in call_args)

    def test_includes_gdb_layer_options(self, tmp_path: Path) -> None:
        src = tmp_path / "adm1.parquet"
        dst = tmp_path / "output.gdb"
        (tmp_path / "output.gdb").mkdir()

        with patch("hdx.scraper.cod_ab_country.formats.run") as mock_run:
            to_multilayer(src, dst, multi=True)

            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "--lco=TARGET_ARCGIS_VERSION=ARCGIS_PRO_3_2_OR_LATER" in call_args

    def test_includes_shp_layer_options(self, tmp_path: Path) -> None:
        src = tmp_path / "adm1.parquet"
        dst = tmp_path / "output.shp.zip"

        with patch("hdx.scraper.cod_ab_country.formats.run") as mock_run:
            to_multilayer(src, dst, multi=True)

            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "--lco=ENCODING=UTF-8" in call_args

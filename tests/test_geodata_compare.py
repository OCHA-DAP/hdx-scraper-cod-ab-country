# flake8: noqa: S101
# ruff: noqa: D102
"""Tests for geodata_compare module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from hdx.scraper.cod_ab_country.geodata.compare import (
    _convert_geodata,
    _download_geodata_from_hdx,
    _is_file_same,
    compare_geodata,
)


class TestDownloadGdbFromHdx:
    """Tests for _download_gdb_from_hdx function."""

    def test_returns_none_when_dataset_not_found(self, tmp_path: Path) -> None:
        with patch(
            "hdx.scraper.cod_ab_country.geodata.compare.Dataset.read_from_hdx",
            return_value=None,
        ):
            result = _download_geodata_from_hdx("test.gdb.zip", "cod-ab-test", tmp_path)
            assert result is None

    def test_returns_none_when_resource_not_found(self, tmp_path: Path) -> None:
        mock_dataset = MagicMock()
        mock_resource = MagicMock()
        mock_resource.__getitem__ = lambda _self, _key: "other.gdb.zip"
        mock_dataset.get_resources.return_value = [mock_resource]

        with patch(
            "hdx.scraper.cod_ab_country.geodata.compare.Dataset.read_from_hdx",
            return_value=mock_dataset,
        ):
            result = _download_geodata_from_hdx("test.gdb.zip", "cod-ab-test", tmp_path)
            assert result is None

    def test_downloads_and_renames_resource(self, tmp_path: Path) -> None:
        downloaded_path = tmp_path / "test.gdb.zip.zip"
        downloaded_path.touch()

        mock_resource = MagicMock()
        mock_resource.__getitem__ = lambda _self, _key: "test.gdb.zip"
        mock_resource.download.return_value = (None, downloaded_path)

        mock_dataset = MagicMock()
        mock_dataset.get_resources.return_value = [mock_resource]

        with patch(
            "hdx.scraper.cod_ab_country.geodata.compare.Dataset.read_from_hdx",
            return_value=mock_dataset,
        ):
            result = _download_geodata_from_hdx("test.gdb.zip", "cod-ab-test", tmp_path)
            assert result == tmp_path / "test.gdb.zip"
            assert result.exists()


class TestConvertGdbToGpkg:
    """Tests for _convert_gdb_to_gpkg function."""

    def test_calls_gdal_with_correct_args(self, tmp_path: Path) -> None:
        gdb_path = tmp_path / "test.gdb"

        with (
            patch(
                "hdx.scraper.cod_ab_country.geodata.compare._list_layers",
                return_value=["layer1"],
            ),
            patch(
                "hdx.scraper.cod_ab_country.geodata.compare.run",
            ) as mock_run,
        ):
            result = _convert_geodata(gdb_path, tmp_path, "x")

            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "gdal" in call_args
            assert "vector" in call_args
            assert "convert" in call_args
            assert gdb_path in call_args
            # assert "--quiet" in call_args
            assert "--overwrite" in call_args
            assert result == tmp_path / "test_x"


class TestIsFileSame:
    """Tests for _is_file_same function."""

    def test_returns_true_for_identical_files(self, tmp_path: Path) -> None:
        file_a = tmp_path / "a.gdb"
        file_b = tmp_path / "b.gdb"
        dir_a = tmp_path / "a_converted"
        dir_b = tmp_path / "b_converted"
        dir_a.mkdir()
        dir_b.mkdir()
        (dir_a / "layer.geojson").write_bytes(b"identical content")
        (dir_b / "layer.geojson").write_bytes(b"identical content")

        with patch(
            "hdx.scraper.cod_ab_country.geodata.compare._convert_geodata",
            side_effect=[dir_a, dir_b],
        ):
            result = _is_file_same(file_a, file_b)
            assert result is True

    def test_returns_false_for_different_files(self, tmp_path: Path) -> None:
        file_a = tmp_path / "a.gdb"
        file_b = tmp_path / "b.gdb"
        dir_a = tmp_path / "a_converted"
        dir_b = tmp_path / "b_converted"
        dir_a.mkdir()
        dir_b.mkdir()
        (dir_a / "layer.geojson").write_bytes(b"content a")
        (dir_b / "layer.geojson").write_bytes(b"content b")

        with patch(
            "hdx.scraper.cod_ab_country.geodata.compare._convert_geodata",
            side_effect=[dir_a, dir_b],
        ):
            result = _is_file_same(file_a, file_b)
            assert result is False


class TestCompareGdb:
    """Tests for compare_gdb function."""

    def test_returns_local_path_when_remote_not_found(self, tmp_path: Path) -> None:
        local_path = tmp_path / "test.gdb.zip"
        local_path.touch()

        with patch(
            "hdx.scraper.cod_ab_country.geodata.compare._download_geodata_from_hdx",
            return_value=None,
        ):
            result = compare_geodata(local_path, "cod-ab-test")
            assert result == local_path

    def test_returns_remote_path_when_files_identical(self, tmp_path: Path) -> None:
        local_path = tmp_path / "test.gdb.zip"
        local_path.touch()
        remote_path = tmp_path / "tmp" / "test.gdb.zip"

        with (
            patch(
                "hdx.scraper.cod_ab_country.geodata.compare._download_geodata_from_hdx",
                return_value=remote_path,
            ),
            patch(
                "hdx.scraper.cod_ab_country.geodata.compare._is_file_same",
                return_value=True,
            ),
        ):
            result = compare_geodata(local_path, "cod-ab-test")
            assert result == remote_path

    def test_returns_local_path_when_files_different(self, tmp_path: Path) -> None:
        local_path = tmp_path / "test.gdb.zip"
        local_path.touch()
        remote_path = tmp_path / "tmp" / "test.gdb.zip"

        with (
            patch(
                "hdx.scraper.cod_ab_country.geodata.compare._download_geodata_from_hdx",
                return_value=remote_path,
            ),
            patch(
                "hdx.scraper.cod_ab_country.geodata.compare._is_file_same",
                return_value=False,
            ),
        ):
            result = compare_geodata(local_path, "cod-ab-test")
            assert result == local_path

    def test_creates_tmp_directory(self, tmp_path: Path) -> None:
        local_path = tmp_path / "test.gdb.zip"
        local_path.touch()

        with patch(
            "hdx.scraper.cod_ab_country.geodata.compare._download_geodata_from_hdx",
            return_value=None,
        ):
            compare_geodata(local_path, "cod-ab-test")
            assert (tmp_path / "tmp").exists()

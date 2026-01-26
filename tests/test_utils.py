# flake8: noqa: S101
# ruff: noqa: D102
"""Tests for utils module."""

from pathlib import Path
from unittest.mock import patch

import pandas as pd

from hdx.scraper.cod_ab_country.utils import get_layer_list, get_metadata


class TestGetLayerList:
    """Tests for get_layer_list function."""

    def test_returns_all_layers_when_no_include_filter(self, tmp_path: Path) -> None:
        metadata_dir = tmp_path / "metadata"
        metadata_dir.mkdir()
        df = pd.DataFrame(
            {
                "country_iso3": ["AFG", "BFA", "CAF"],
                "version": ["v1", "v2", "v1"],
            },
        )
        df.to_parquet(metadata_dir / "metadata_latest.parquet")

        with patch("hdx.scraper.cod_ab_country.utils.iso3_include", []):
            result = get_layer_list(tmp_path)
            assert result == [("AFG", "v1"), ("BFA", "v2"), ("CAF", "v1")]

    def test_filters_by_iso3_include(self, tmp_path: Path) -> None:
        metadata_dir = tmp_path / "metadata"
        metadata_dir.mkdir()
        df = pd.DataFrame(
            {
                "country_iso3": ["AFG", "BFA", "CAF"],
                "version": ["v1", "v2", "v1"],
            },
        )
        df.to_parquet(metadata_dir / "metadata_latest.parquet")

        with patch("hdx.scraper.cod_ab_country.utils.iso3_include", ["AFG", "CAF"]):
            result = get_layer_list(tmp_path)
            assert result == [("AFG", "v1"), ("CAF", "v1")]

    def test_handles_version_specific_include(self, tmp_path: Path) -> None:
        metadata_dir = tmp_path / "metadata"
        metadata_dir.mkdir()
        df = pd.DataFrame(
            {
                "country_iso3": ["AFG", "BFA"],
                "version": ["v1", "v2"],
            },
        )
        df.to_parquet(metadata_dir / "metadata_latest.parquet")

        with patch("hdx.scraper.cod_ab_country.utils.iso3_include", ["AFG_V3"]):
            result = get_layer_list(tmp_path)
            assert result == [("AFG", "v3")]


class TestGetMetadata:
    """Tests for get_metadata function."""

    def test_returns_metadata_for_country(self, tmp_path: Path) -> None:
        metadata_dir = tmp_path / "metadata"
        metadata_dir.mkdir()
        df = pd.DataFrame(
            {
                "country_iso3": ["AFG", "BFA", "CAF"],
                "version": ["v1", "v2", "v1"],
                "source": ["Source A", "Source B", "Source C"],
            },
        )
        df.to_parquet(metadata_dir / "metadata_all.parquet")

        result = get_metadata(tmp_path, "BFA", "v2")
        assert result["country_iso3"] == "BFA"
        assert result["version"] == "v2"
        assert result["source"] == "Source B"

    def test_returns_empty_dict_when_not_found(self, tmp_path: Path) -> None:
        metadata_dir = tmp_path / "metadata"
        metadata_dir.mkdir()
        df = pd.DataFrame(
            {
                "country_iso3": ["AFG"],
                "version": ["v1"],
            },
        )
        df.to_parquet(metadata_dir / "metadata_all.parquet")

        result = get_metadata(tmp_path, "XXX", "v1")
        assert result == {}

    def test_filters_by_both_iso3_and_version(self, tmp_path: Path) -> None:
        metadata_dir = tmp_path / "metadata"
        metadata_dir.mkdir()
        df = pd.DataFrame(
            {
                "country_iso3": ["AFG", "AFG", "AFG"],
                "version": ["v1", "v2", "v3"],
                "data": ["first", "second", "third"],
            },
        )
        df.to_parquet(metadata_dir / "metadata_all.parquet")

        result = get_metadata(tmp_path, "AFG", "v2")
        assert result["data"] == "second"

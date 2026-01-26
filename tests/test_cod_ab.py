# flake8: noqa: S101, PTH118, PTH207
# ruff: noqa: ARG002, PLR2004

from datetime import date
from glob import glob
from os.path import join
from pathlib import Path
from shutil import copy2
from unittest.mock import patch

from hdx.utilities.path import temp_dir

from hdx.scraper.cod_ab_country.dataset import generate_dataset


class TestCODAB:
    """Test class."""

    def test_generate_dataset(
        self,
        configuration: None,
        fixtures_dir: str,
    ) -> None:
        """Test generate_dataset function."""
        with temp_dir(
            "Test_cod_ab",
            delete_on_success=True,
            delete_on_failure=False,
        ) as tempdir:
            iso3 = "CAF"
            iso3_dir = Path(tempdir) / iso3.lower()
            iso3_dir.mkdir(exist_ok=True, parents=True)

            # Copy parquet files to temp dir
            parquet_files = glob(f"{join(fixtures_dir, iso3.lower())}/*.parquet")
            for parquet_file in parquet_files:
                copy2(parquet_file, iso3_dir)

            # Copy pre-built output files
            for ext in ["xlsx", "gdb.zip", "shp.zip", "geojson.zip"]:
                src = Path(fixtures_dir) / iso3.lower() / f"{iso3.lower()}_cod_ab.{ext}"
                if src.exists():
                    copy2(src, iso3_dir / f"{iso3.lower()}_admin_boundaries.{ext}")

            # Create mock output files if they don't exist
            for ext in ["xlsx", "gdb.zip", "shp.zip", "geojson.zip"]:
                output_file = iso3_dir / f"{iso3.lower()}_admin_boundaries.{ext}"
                if not output_file.exists():
                    output_file.touch()

            metadata = {
                "version": "v1",
                "date_valid_on": date(2020, 12, 1),
                "date_reviewed": date(2024, 3, 1),
                "date_updated": date(2024, 2, 15),
                "date_source": date(2020, 11, 1),
                "update_frequency": 1,
                "source": "Agency for Technical Cooperation and Development (ACTED)",
                "contributor": "OCHA Central African Republic",
                "methodology_dataset": "Prepared by UN-OCHA",
                "methodology_pcodes": None,
                "caveats": None,
                "admin_level_max": 4,
                "admin_level_full": 4,
                "admin_notes": None,
                "admin_1_count": 17,
                "admin_1_name": "Prefecture",
                "admin_2_count": 72,
                "admin_2_name": "Sub-prefecture",
                "admin_3_count": 175,
                "admin_3_name": "Commune",
                "admin_4_count": 202,
                "admin_4_name": "Locality",
            }

            # Mock compare_gdb to return local path (skip HDX download)
            with patch(
                "hdx.scraper.cod_ab_country.dataset.compare_gdb",
                side_effect=lambda path, _: path,
            ):
                dataset = generate_dataset(iso3_dir, iso3, metadata)

            assert dataset is not None
            assert dataset["name"] == "cod-ab-caf"
            assert (
                dataset["title"]
                == "Central African Republic - Subnational Administrative Boundaries"
            )
            assert (
                dataset["dataset_date"]
                == "[2020-12-01T00:00:00 TO 2024-03-01T23:59:59]"
            )
            assert dataset["data_update_frequency"] == 365
            assert {"name": "caf"} in dataset["groups"]

            # Check tags
            tag_names = [t["name"] for t in dataset["tags"]]
            assert "administrative boundaries-divisions" in tag_names
            assert "gazetteer" in tag_names

            # Check resources
            resources = dataset.get_resources()
            assert len(resources) == 4
            resource_names = [r["name"] for r in resources]
            assert "caf_admin_boundaries.gdb.zip" in resource_names
            assert "caf_admin_boundaries.shp.zip" in resource_names
            assert "caf_admin_boundaries.geojson.zip" in resource_names
            assert "caf_admin_boundaries.xlsx" in resource_names

            # Check notes content
            notes = dataset["notes"]
            assert "Central African Republic" in notes
            assert "administrative level 0-4" in notes
            assert "Prefecture" in notes
            assert "Sub-prefecture" in notes

    def test_generate_dataset_returns_none_for_invalid_iso3(
        self,
        configuration: None,
    ) -> None:
        """Test that generate_dataset returns None for invalid ISO3."""
        with temp_dir("Test_invalid", delete_on_success=True) as tempdir:
            iso3_dir = Path(tempdir)
            metadata = {"date_valid_on": date(2020, 1, 1)}

            dataset = generate_dataset(iso3_dir, "XXX", metadata)
            assert dataset is None

    def test_generate_dataset_returns_none_for_missing_dates(
        self,
        configuration: None,
    ) -> None:
        """Test that generate_dataset returns None when dates are missing."""
        with temp_dir("Test_no_dates", delete_on_success=True) as tempdir:
            iso3_dir = Path(tempdir)
            metadata = {
                "date_valid_on": None,
                "date_reviewed": None,
            }

            dataset = generate_dataset(iso3_dir, "CAF", metadata)
            assert dataset is None

# COD-AB Metadata Specification

Version: 0.1.0-draft

## Overview

This specification defines the format and schema for the distribution of COD-AB (Common Operational Dataset – Administrative Boundaries) metadata. The metadata tables provide a registry of all country boundary datasets, including version history, administrative level structure, dates, provenance, and methodological notes.

The key words "MUST", "REQUIRED", "SHALL", "SHOULD", "RECOMMENDED", and "MAY" in this document are to be interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

## Schema

### Country Identifier Columns

| Column         | Type    | Nullable | Notes                                           |
| -------------- | ------- | -------- | ----------------------------------------------- |
| `country_name` | VARCHAR | No       | Country name in English                         |
| `country_iso2` | VARCHAR | No       | ISO 3166-1 alpha-2 code (e.g. `AF`)             |
| `country_iso3` | VARCHAR | No       | ISO 3166-1 alpha-3 code (e.g. `AFG`), uppercase |
| `version`      | VARCHAR | No       | Dataset version string (e.g. `v01`, `v02`)      |

`country_iso3` and `version` together form a unique key.

### Admin Level Columns

| Column             | Type    | Nullable | Notes                                                        |
| ------------------ | ------- | -------- | ------------------------------------------------------------ |
| `admin_level_full` | INTEGER | No       | Highest admin level with complete national coverage (1–4)    |
| `admin_level_max`  | BIGINT  | No       | Deepest admin level present in the boundary data (≥ 1)       |
| `admin_1_name`     | VARCHAR | Yes      | Local name for the admin 1 concept (e.g. `Province`)         |
| `admin_2_name`     | VARCHAR | Yes      | Local name for the admin 2 concept (e.g. `District`)         |
| `admin_3_name`     | VARCHAR | Yes      | Local name for the admin 3 concept, nullable                 |
| `admin_4_name`     | VARCHAR | Yes      | Local name for the admin 4 concept, nullable                 |
| `admin_5_name`     | VARCHAR | Yes      | Local name for the admin 5 concept, nullable                 |
| `admin_1_count`    | INTEGER | No       | Number of admin level 1 units                                |
| `admin_2_count`    | INTEGER | Yes      | Number of admin level 2 units; null if level absent          |
| `admin_3_count`    | INTEGER | Yes      | Number of admin level 3 units; null if level absent          |
| `admin_4_count`    | INTEGER | Yes      | Number of admin level 4 units; null if level absent          |
| `admin_5_count`    | INTEGER | Yes      | Number of admin level 5 units; null if level absent          |
| `admin_notes`      | VARCHAR | Yes      | Free-text notes about the administrative structure, nullable |

`admin_level_full` MUST be less than or equal to `admin_level_max`. When `admin_level_full` < `admin_level_max`, the deeper levels exist in the boundary data but do not cover the entire country. `admin_level_full` defaults to `admin_level_max` and is only overridden where known to differ.

`admin_{N}_count` MUST be null when `admin_level_max` < N. `admin_{N}_count` MUST be non-null when `admin_level_max` ≥ N.

`admin_{N}_name` values give the local concept name (e.g. "Province", "District"), not an individual unit name. They are nullable; when unknown they are stored as null.

> **Note:** In current data many string columns use an empty string (`''`) rather than null to represent an absent value. Parsers SHOULD treat empty string as equivalent to null for these columns. See [Known Deviations](#known-deviations).

### Date Columns

| Column          | Type | Nullable | Notes                                                      |
| --------------- | ---- | -------- | ---------------------------------------------------------- |
| `date_source`   | DATE | Yes      | Date of the original source data                           |
| `date_updated`  | DATE | Yes      | Date the dataset was last updated by the contributor       |
| `date_reviewed` | DATE | Yes      | Date the dataset was last reviewed by OCHA                 |
| `date_metadata` | DATE | Yes      | Date the metadata record was last updated                  |
| `date_valid_on` | DATE | Yes      | Date from which this dataset version is considered valid   |
| `date_valid_to` | DATE | Yes      | Date on which this version was superseded; null if current |

### Update Columns

| Column             | Type    | Nullable | Notes                                            |
| ------------------ | ------- | -------- | ------------------------------------------------ |
| `update_frequency` | BIGINT  | No       | Update frequency of source in years (1 or 2)     |
| `update_type`      | VARCHAR | Yes      | Nature of last update: `major`, `minor`, or null |

`update_type` is almost always `major`; `minor` updates indicate schema-compatible changes that do not alter administrative boundaries.

### Provenance Columns

| Column                | Type    | Nullable | Notes                                            |
| --------------------- | ------- | -------- | ------------------------------------------------ |
| `source`              | VARCHAR | No       | Source organisation(s) that produced the data    |
| `contributor`         | VARCHAR | No       | OCHA office or team that processed and published |
| `methodology_dataset` | VARCHAR | No       | Description of how the dataset was produced      |
| `methodology_pcodes`  | VARCHAR | Yes      | Description of the p-code assignment methodology |
| `caveats`             | VARCHAR | No       | Caveats about data quality, coverage, or history |

`source`, `contributor`, `methodology_dataset`, and `caveats` are always present (never null) but may be empty strings when the information is not available.

`methodology_pcodes` is typically an empty string and is non-null in only a small number of records.

## Column Order

Columns MUST appear in the following order:

1. `country_name`, `country_iso2`, `country_iso3`, `version`
2. `admin_level_full`, `admin_level_max`
3. `admin_1_name`, `admin_2_name`, `admin_3_name`, `admin_4_name`, `admin_5_name`
4. `admin_1_count`, `admin_2_count`, `admin_3_count`, `admin_4_count`, `admin_5_count`
5. `admin_notes`
6. `date_source`, `date_updated`, `date_reviewed`, `date_metadata`, `date_valid_on`, `date_valid_to`
7. `update_frequency`, `update_type`
8. `source`, `contributor`, `methodology_dataset`, `methodology_pcodes`, `caveats`

## Known Deviations

This specification describes the intended schema. The current dataset has the following known deviations:

- **Empty string vs null**: Many string columns use an empty string (`''`) to represent absent data rather than null. This is most prevalent in `admin_5_name`, `admin_notes`, `caveats`, and `methodology_pcodes`. A future release SHOULD normalise these to null.
- **`admin_1_name` through `admin_5_name` inconsistency**: These columns mix null and empty string to represent absence depending on how the source metadata was recorded.
- **`admin_level_full` type**: Stored as `INTEGER` (nullable `Int32`) rather than `BIGINT` like `admin_level_max`. These SHOULD use the same integer type.
- **`caveates` source column**: The upstream ArcGIS metadata table uses the misspelled column name `caveates`; the pipeline renames it to `caveats` during processing.

## Appendix: Example Rows

One row for Afghanistan:

```text
country_name        Afghanistan
country_iso2        AF
country_iso3        AFG
version             v01
admin_level_full    2
admin_level_max     2
admin_1_name        Province
admin_2_name        District
admin_3_name        (empty)
admin_4_name        (empty)
admin_5_name        (empty)
admin_1_count       34
admin_2_count       399
admin_3_count       NULL
admin_4_count       NULL
admin_5_count       NULL
admin_notes         (empty)
date_source         2019-10-22
date_updated        NULL
date_reviewed       NULL
date_metadata       2025-10-22
date_valid_on       2018-05-22
date_valid_to       2021-11-17     ← non-null: this version was superseded
update_frequency    1
update_type         major
source              Afghanistan Geodesy and Cartography Head Office (AGCHO)
contributor         OCHA Field Information Services Section (FISS)
methodology_dataset FISS processing
methodology_pcodes  (empty)
caveats             (empty)
```

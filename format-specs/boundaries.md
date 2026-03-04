# COD-AB Specification

Version: 0.1.0-draft

## Overview

The Common Operational Dataset – Administrative Boundaries (COD-AB) is a collection of administrative boundary datasets published by the United Nations Office for the Coordination of Humanitarian Affairs (UN OCHA). This specification defines the format and schema for the distribution of these datasets.

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

## Background

COD-ABs are the authoritative administrative boundary datasets for humanitarian response. They are maintained on a country-by-country basis, versioned over time, and cover up to six administrative levels (Admin 0–5). Each country may have one or more versioned datasets.

## File Layout

The file layout is:

```text
cod_ab_{iso3}_{version}/    # one directory per country version
  {iso3}_admin0             # admin level 0 (country)
  {iso3}_admin1             # admin level 1
  {iso3}_admin2             # admin level 2 (if present)
  {iso3}_admin3             # admin level 3 (if present)
  {iso3}_admin4             # admin level 4 (if present)
  {iso3}_admin5             # admin level 5 (if present)
  {iso3}_adminlines         # boundary lines (if present)
  {iso3}_adminpoints        # administrative points (if present)
  {iso3}_admincapitals      # administrative capitals (if present)
```

### Directory Naming

Each versioned country dataset has its own directory named `cod_ab_{iso3}_{version}` where:

- `{iso3}` is the [ISO 3166-1 alpha-3](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-3) country code in lowercase (e.g., `afg`, `eth`)
- `{version}` is the dataset version, formatted as `v{NN}` (e.g., `v01`, `v02`)

> **Note:** Some existing directories use the format `v_{NN}` (e.g., `cod_ab_blr_v_01`). This is a legacy naming convention. New datasets SHOULD use the `v{NN}` format.

### File Naming

Each admin boundary file is named `{iso3}_admin{N}` where `{N}` is the integer admin level (0–5). The ISO3 code MUST be lowercase. Admin level 0 (country boundary) and Admin level 1 MUST be present; higher levels are present only if the country has data at that level. Admin levels MUST be contiguous: if level N is present, levels 0 through N-1 MUST also be present.

### Coordinate Reference System

All geometries MUST use [EPSG:4326](https://epsg.io/4326) (WGS 84, geographic latitude/longitude).

## Admin Boundary Layers (`{iso3}_admin{N}`)

Each admin boundary file represents one administrative level for one country version. Every row in the file is a single administrative unit (polygon) at that level.

### Name Columns

Each admin level N file contains name columns for all ancestor levels 0 through N. For each level L (0 ≤ L ≤ N):

| Column         | Type   | Max length | Notes                                                     |
| -------------- | ------ | ---------- | --------------------------------------------------------- |
| `adm{L}_name`  | string | 100        | Name in the primary language (`lang`)                     |
| `adm{L}_name1` | string | 100        | Name in the first alternate language (`lang1`), nullable  |
| `adm{L}_name2` | string | 100        | Name in the second alternate language (`lang2`), nullable |
| `adm{L}_name3` | string | 100        | Name in the third alternate language (`lang3`), nullable  |

`adm{L}_name` MUST be present and non-null for all rows. `adm{L}_name1`, `adm{L}_name2`, and `adm{L}_name3` are REQUIRED columns but MAY contain null values. A name column MUST be null if the corresponding language column (`lang1`, `lang2`, `lang3`) is null.

### P-Code Columns

For each level L (0 ≤ L ≤ N):

| Column         | Type   | Max length | Notes                                             |
| -------------- | ------ | ---------- | ------------------------------------------------- |
| `adm{L}_pcode` | string | 20         | Place code for the administrative unit at level L |

P-codes (place codes) are alphanumeric strings that uniquely identify an administrative unit. P-codes MUST be hierarchically nested: `adm{L}_pcode` MUST start with `adm{L-1}_pcode` for all L > 0. All p-codes in a column MUST be unique within the file (no duplicates at the same level). P-codes MUST be alphanumeric only (letters and digits, no spaces or special characters).

The admin 0 p-code (`adm0_pcode`) SHOULD equal the country's [ISO 3166-1 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) code (e.g., `AF` for Afghanistan).

### Language Columns

Language codes identify which language each name column is written in:

| Column  | Type   | Max length | Notes                                                    |
| ------- | ------ | ---------- | -------------------------------------------------------- |
| `lang`  | string | 3          | BCP 47 language tag for `adm{L}_name` columns            |
| `lang1` | string | 3          | BCP 47 language tag for `adm{L}_name1` columns, nullable |
| `lang2` | string | 3          | BCP 47 language tag for `adm{L}_name2` columns, nullable |
| `lang3` | string | 3          | BCP 47 language tag for `adm{L}_name3` columns, nullable |

Language tags MUST be valid [BCP 47](https://www.rfc-editor.org/rfc/rfc5646) language tags. All rows in a file MUST share the same values for `lang`, `lang1`, `lang2`, and `lang3` (language codes are constant per layer). `lang` MUST be non-null and MUST be a romanized language (e.g. English, French, Spanish, Portuguese). `lang1`, `lang2`, and `lang3` are nullable; a language column being null means that alternate language is absent from the dataset.

### Date Columns

| Column     | Type                    | Notes                                                                 |
| ---------- | ----------------------- | --------------------------------------------------------------------- |
| `valid_on` | timestamp with timezone | When this version of the data was last updated                        |
| `valid_to` | timestamp               | When this version was superseded; null if this is the current version |

All rows in a file SHOULD share the same `valid_on` and `valid_to` values (dates are constant per layer). `valid_on` MUST be non-null. `valid_to` MUST be null for the current (latest) version of a dataset and non-null for retired versions.

> **Note:** `valid_to` has inconsistent timezone handling in existing data (some files store it as timestamp with timezone, others as timestamp without). New data SHOULD use timestamp with timezone consistently.

### Computed Columns

| Column       | Type   | Notes                                                         |
| ------------ | ------ | ------------------------------------------------------------- |
| `area_sqkm`  | double | Area of the polygon in square kilometres                      |
| `center_lat` | double | Latitude of a representative point guaranteed within polygon  |
| `center_lon` | double | Longitude of a representative point guaranteed within polygon |

These values are computed from the geometry. `area_sqkm` is computed in an equal-area projection (EPSG:6933). `center_lat` and `center_lon` are geographic coordinates (EPSG:4326) of a point guaranteed to be within the polygon.

`center_lat` and `center_lon` SHOULD be generated using a Maximum Inscribed Circle (MIC) algorithm, which finds the largest circle that fits inside the polygon and uses its center as the representative point. Implementations include DuckDB's [`ST_MaximumInscribedCircle`](https://duckdb.org/docs/stable/core_extensions/spatial/functions#st_maximuminscribedcircle) and GeoPandas' [`GeoSeries.maximum_inscribed_circle`](https://geopandas.org/en/stable/docs/reference/api/geopandas.GeoSeries.maximum_inscribed_circle.html). Many existing datasets use a simple centroid instead, which does not guarantee that the point falls within the polygon (e.g. for concave or donut-shaped polygons).

### Version Column

One of the following MUST be present:

| Column        | Type   | Notes                                  |
| ------------- | ------ | -------------------------------------- |
| `version`     | string | Version string, e.g. `v01` (preferred) |
| `cod_version` | string | Legacy version string, e.g. `V_01`     |

The preferred column name is `version`. The `cod_version` column is a legacy variant present in some older datasets. New datasets MUST use `version`.

### Identifier Columns (Admin 0 only)

These columns are present only on admin level 0 files:

| Column | Type   | Max length | Notes                                       |
| ------ | ------ | ---------- | ------------------------------------------- |
| `iso2` | string | 2          | ISO 3166-1 alpha-2 country code, e.g. `AF`  |
| `iso3` | string | 3          | ISO 3166-1 alpha-3 country code, e.g. `AFG` |

> **Note:** `iso2` and `iso3` appear only in admin 0 files in current data. They SHOULD be included in higher admin levels to keep schemas consistent.

### Reference Name Column (Deprecated)

> **Deprecated:** The `adm{N}_ref_name` column (also seen as `adm{N}_ref_name1`) is deprecated and SHOULD NOT be included in new datasets. Existing data containing this column MUST NOT cause parsers to fail, but it should be omitted going forward.

| Column            | Type   | Notes                                                              |
| ----------------- | ------ | ------------------------------------------------------------------ |
| `adm{N}_ref_name` | string | Romanized or UN official reference name for the current-level unit |

This column, when present, contains the preferred reference name for the administrative unit at the current level (level N). It is typically the romanized Latin-script form when the primary script is non-Latin. Only the current level's ref name is included, not ancestors.

### Non-Standard Columns

Datasets MAY include additional columns not defined in this specification (e.g., `regionname_en`, `regioncode`, `unittype`). Such columns MUST be placed after all standard columns and SHOULD be documented by the data producer. Parsers MUST NOT fail when encountering non-standard columns.

### Column Order

Columns SHOULD appear in the following order within each file:

1. `adm{N}_name`, `adm{N}_name1`, `adm{N}_name2`, `adm{N}_name3`, `adm{N}_pcode` (current level, descending from N to 0)
2. Ancestor name and p-code columns (level N-1 down to 0)
3. `valid_on`, `valid_to`
4. `area_sqkm`, `version` (or `cod_version`)
5. `lang`, `lang1`, `lang2`, `lang3`
6. `adm{N}_ref_name` (if present)
7. `iso2`, `iso3` (admin 0 only)
8. `center_lat`, `center_lon`

## Supplementary Layers

### Admin Lines (`{iso3}_adminlines`)

Boundary line representations of the administrative units. These are derived from the admin boundary polygons and may not be present for all countries.

| Column       | Type                    | Notes                                        |
| ------------ | ----------------------- | -------------------------------------------- |
| `adm_level`  | int16                   | Admin level this boundary segment represents |
| `name`       | string                  | Name of the boundary segment                 |
| `valid_on`   | timestamp with timezone | See date columns above                       |
| `valid_to`   | timestamp               | See date columns above                       |
| `version`    | string                  | See version column above                     |
| `right_pcod` | string                  | P-code of the unit to the right of the line  |
| `left_pcod`  | string                  | P-code of the unit to the left of the line   |

### Admin Points (`{iso3}_adminpoints`)

Point representations of administrative units (e.g. label points). Schema varies by country and is not yet standardized. Where these points serve as representative points for polygons, they SHOULD be generated using a Maximum Inscribed Circle (MIC) algorithm, consistent with the `center_lat`/`center_lon` columns described above.

### Admin Capitals (`{iso3}_admincapitals`)

Point locations of administrative capital cities. Schema varies by country and is not yet standardized.

## Known Deviations in Current Data

This specification describes the intended schema. The current dataset has the following known deviations that should be addressed in future releases:

- **`cod_version` vs `version`**: Some datasets (those with `v_` in the directory name) use `cod_version` instead of `version`, and the value format differs (`V_01` vs `v01`).
- **`adm{N}_ref_name1`**: A few datasets use `adm{N}_ref_name1` instead of `adm{N}_ref_name`. These should be renamed.
- **`valid_to` timezone**: Some files store `valid_to` without a timezone, others with UTC. This should be standardised to always include UTC.
- **`center_lat`/`center_lon` missing**: A small number of files are missing these columns (e.g., `cod_ab_dza_v01`).
- **Non-standard columns**: Some files contain extra columns outside this spec (e.g., `regionname_en`, `regioncode`, `unittype` in Afghanistan admin 2).
- **Admin lines, points, and capitals**: These supplementary layers have inconsistent schemas across countries and are not yet fully standardised.

## Appendix: Example Column Set

For an admin level 2 file with English primary and Dari secondary language:

```text
adm2_name         (string, primary name in English)
adm2_name1        (string, name in Dari, nullable)
adm2_name2        (string, nullable)
adm2_name3        (string, nullable)
adm2_pcode        (string, e.g. "AF1113")
adm1_name         (string, parent admin 1 name)
adm1_name1        (string, nullable)
adm1_name2        (string, nullable)
adm1_name3        (string, nullable)
adm1_pcode        (string, e.g. "AF11")
adm0_name         (string, country name)
adm0_name1        (string, nullable)
adm0_name2        (string, nullable)
adm0_name3        (string, nullable)
adm0_pcode        (string, e.g. "AF")
valid_on          (timestamp with timezone)
valid_to          (timestamp with timezone, nullable)
area_sqkm         (double)
version           (string, e.g. "v01")
lang              (string, e.g. "en")
lang1             (string, e.g. "da", nullable)
lang2             (string, nullable)
lang3             (string, nullable)
adm2_ref_name     (string, nullable)
center_lat        (double)
center_lon        (double)
```

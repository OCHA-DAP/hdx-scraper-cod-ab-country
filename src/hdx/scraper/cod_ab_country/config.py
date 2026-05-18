"""Runtime configuration and environment settings."""

import logging
import subprocess
from os import environ, getenv

from dotenv import load_dotenv

load_dotenv(override=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logging.getLogger("httpx").setLevel(logging.WARNING)

environ["OGR_GEOJSON_MAX_OBJ_SIZE"] = "0"
environ["OGR_ORGANIZE_POLYGONS"] = "ONLY_CCW"
environ["PYOGRIO_USE_ARROW"] = "1"


def _gdal_version() -> tuple[int, ...]:
    try:
        out = subprocess.check_output(["gdal-config", "--version"], text=True).strip()
        return tuple(int(x) for x in out.split(".")[:2])
    except (OSError, ValueError, subprocess.SubprocessError):
        return (0, 0)


OCHA_ORG_NAME = "OCHA Field Information Services Section (FISS)"

OBJECTID = "esriFieldTypeOID"
GLOBALID = "esriFieldTypeGlobalID"

ARCGIS_SERVER = getenv("ARCGIS_SERVER", "https://gis.unocha.org")
ARCGIS_USERNAME = getenv("ARCGIS_USERNAME", "")
ARCGIS_PASSWORD = getenv("ARCGIS_PASSWORD", "")
ARCGIS_FOLDER = getenv("ARCGIS_FOLDER", "Hosted")
ARCGIS_SERVICE_URL = f"{ARCGIS_SERVER}/server/rest/services/{ARCGIS_FOLDER}"
ARCGIS_METADATA = getenv("ARCGIS_METADATA", "COD_Global_Metadata")
ARCGIS_METADATA_SERVICE_URL = f"{ARCGIS_SERVICE_URL}/{ARCGIS_METADATA}/FeatureServer"
ARCGIS_METADATA_URL = f"{ARCGIS_METADATA_SERVICE_URL}/0"

ATTEMPT = int(getenv("ATTEMPT", "5"))
WAIT = int(getenv("WAIT", "10"))
TIMEOUT = int(getenv("TIMEOUT", "60"))
EXPIRATION = int(getenv("EXPIRATION", "1440"))  # minutes (1 day)

ISO3_EXCLUDE_DEFAULTS = "COL,ECU,IDN,MAF,PHL,QAT,SSD"

TEMP_DIR = getenv("TEMP_DIR", ".")

iso3_include_cfg = [
    x.strip() for x in getenv("ISO3_INCLUDE", "").upper().split(",") if x.strip()
]
iso3_exclude_cfg = [
    x.strip()
    for x in getenv("ISO3_EXCLUDE", ISO3_EXCLUDE_DEFAULTS).upper().split(",")
    if x.strip()
]

_gdal_ver = _gdal_version()

gdal_parquet_options = [
    "--overwrite",
    "--lco=COMPRESSION=ZSTD",
]

if _gdal_ver >= (3, 12):
    gdal_parquet_options += [
        "--quiet",
        "--lco=USE_PARQUET_GEO_TYPES=YES",
        "--lco=COMPRESSION_LEVEL=15",
    ]

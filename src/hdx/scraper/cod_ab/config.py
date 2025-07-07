import logging
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

ARCGIS_SERVER = getenv("ARCGIS_SERVER", "")
ARCGIS_USERNAME = getenv("ARCGIS_USERNAME", "")
ARCGIS_PASSWORD = getenv("ARCGIS_PASSWORD", "")

DEBUG = getenv("DEBUG", "").lower() in ("true", "1", "yes", "on")

ATTEMPT = int(getenv("ATTEMPT", "5"))
WAIT = int(getenv("WAIT", "10"))
TIMEOUT = int(getenv("TIMEOUT", "60"))
TIMEOUT_DOWNLOAD = int(getenv("TIMEOUT_DOWNLOAD", "600"))
ADMIN_LEVELS = int(getenv("ADMIN_LEVELS", "5"))

LANGUAGE_COUNT = 4
EPSG_EQUAL_AREA = 6933
EPSG_WGS84 = 4326
GEOJSON_PRECISION = 6
METERS_PER_KM = 1_000_000
PLOTLY_SIMPLIFY = 0.000_01
POLYGON = "Polygon"
SLIVER_GAP_AREA_KM = 0.000_1
SLIVER_GAP_THINNESS = 0.001
VALID_GEOMETRY = "Valid Geometry"
VALID_ON = "valid_on"
VALID_TO = "valid_to"

services_url = f"{ARCGIS_SERVER}/server/rest/services/Hosted"

checks_config = {
    "max_level": {
        "CAF": 3,
        "MMR": 3,
        "TCD": 2,
        "UKR": 3,
    },
}

misc_columns = [
    "area_sqkm",
    "geometry",
    "iso2",
    "iso3",
    "lang",
    "lang1",
    "lang2",
    "lang3",
    "valid_on",
    "valid_to",
    "version_no",
]

official_languages = ["ar", "en", "es", "fr", "ru", "zh"]
romanized_languages = ["en", "es", "fr", "hu", "id", "nl", "pl", "pt", "ro", "sk"]

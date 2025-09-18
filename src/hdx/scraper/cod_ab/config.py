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

OBJECTID = "esriFieldTypeOID"

ARCGIS_SERVER = getenv("ARCGIS_SERVER", "https://gis.unocha.org")
ARCGIS_USERNAME = getenv("ARCGIS_USERNAME", "")
ARCGIS_PASSWORD = getenv("ARCGIS_PASSWORD", "")
ARCGIS_FOLDER = getenv("ARCGIS_FOLDER", "Hosted")
ARCGIS_SERVICE_URL = f"{ARCGIS_SERVER}/server/rest/services/{ARCGIS_FOLDER}"
ARCGIS_SERVICE_REGEX = getenv("ARCGIS_SERVICE_REGEX", "cod_ab_[a-z]{3}_v_[0-9]{2}$")
ARCGIS_METADATA = getenv("ARCGIS_METADATA", "COD_Global_Metadata")
ARCGIS_METADATA_URL = f"{ARCGIS_SERVICE_URL}/{ARCGIS_METADATA}/FeatureServer/0"

ATTEMPT = int(getenv("ATTEMPT", "5"))
WAIT = int(getenv("WAIT", "10"))
TIMEOUT = int(getenv("TIMEOUT", "60"))
TIMEOUT_DOWNLOAD = int(getenv("TIMEOUT_DOWNLOAD", "600"))
EXPIRATION = int(getenv("EXPIRATION", "1440"))  # minutes (1 day)

ISO_3_LEN = 3
iso3_include = [
    x for x in getenv("ISO3_INCLUDE", "").upper().split(",") if len(x) == ISO_3_LEN
]
iso3_exclude = [
    x for x in getenv("ISO3_EXCLUDE", "").upper().split(",") if len(x) == ISO_3_LEN
]

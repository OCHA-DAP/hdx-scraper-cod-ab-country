from geopandas import GeoDataFrame
from hdx.location.country import Country
from icu import USET_ADD_CASE_MAPPINGS, LocaleData, ULocaleDataExemplarSetType
from langcodes import tag_is_valid

from .table_names_config import auxiliary_codes, exclude_check, punctuation_set
from hdx.scraper.cod_ab.config import LANGUAGE_COUNT, official_languages


def get_languages(gdf: GeoDataFrame) -> list[str]:
    """Get a list of language codes used in the dataset."""
    lang_codes = []
    for index in range(LANGUAGE_COUNT):
        lang_col = f"lang{index}" if index > 0 else "lang"
        codes = gdf[~gdf[lang_col].isna()][lang_col].drop_duplicates()
        lang_codes.extend(codes)
    return lang_codes


def get_char_set(lang: str, iso3: str) -> list[str]:
    """Get character set for a language code."""
    return [
        x
        for y in LocaleData(lang).getExemplarSet(
            USET_ADD_CASE_MAPPINGS,
            ULocaleDataExemplarSetType.ES_STANDARD,
        )
        for x in y
    ] + [chr(int(x[2:], 16)) for x in auxiliary_codes.get(f"{lang}-{iso3}", [])]


def get_invalid_chars(lang: str, name: str | None, iso3: str) -> str:
    """Check if a value within a column is a valid name based on it's language code."""
    if (
        not isinstance(name, str)
        or not name.strip()
        or not tag_is_valid(lang)
        or lang in exclude_check
    ):
        return ""
    char_set = get_char_set(lang, iso3)
    return "".join({char for char in name if char not in char_set + punctuation_set})


def is_invalid_adm0(lang: str, name: str | None, iso3: str) -> bool:
    """Checks if Admin 0 name is invalid."""
    if lang not in official_languages:
        return False
    country_info = Country.get_country_info_from_iso3(iso3)
    if not country_info:
        return False
    official_name = country_info[f"#country+alt+i_{lang}+name+v_m49"]
    return name != official_name


def is_upper(name: str | None) -> bool:
    """Checks if name is all uppercase."""
    if not isinstance(name, str) or not name.strip():
        return False
    return name == name.upper() and name.lower() != name.upper()


def is_lower(name: str | None) -> bool:
    """Checks if name is all lowercase."""
    if not isinstance(name, str) or not name.strip():
        return False
    return name == name.lower() and name.lower() != name.upper()


def has_numbers(name: str | None) -> bool:
    """Checks if name has numbers."""
    if not isinstance(name, str) or not name.strip():
        return False
    return any(char.isdigit() for char in name)


def is_punctuation(lang: str, name: str | None, iso3: str) -> bool:
    """Check if a value within a column is a valid name based on it's language code."""
    if (
        not isinstance(name, str)
        or not name.strip()
        or not tag_is_valid(lang)
        or lang in exclude_check
    ):
        return False
    char_set = get_char_set(lang, iso3)
    return all(char not in char_set for char in name)


def is_invalid(lang: str, name: str | None, iso3: str) -> bool:
    """Check if a value within a column is a valid name based on it's language code."""
    if (
        not isinstance(name, str)
        or not name.strip()
        or not tag_is_valid(lang)
        or lang in exclude_check
    ):
        return False
    char_set = get_char_set(lang, iso3)
    return any(char not in char_set + punctuation_set for char in name)


def has_double_spaces(name: str | None) -> bool:
    """Checks if string has double spaces."""
    if not isinstance(name, str) or not name.strip():
        return False
    return "  " in name


def has_strippable_spaces(name: str | None) -> bool:
    """Checks if string has strippable spaces."""
    if not isinstance(name, str) or not name.strip():
        return False
    return name != name.strip()

OBJECTID = "esriFieldTypeOID"


def parse_fields(fields: list) -> tuple[str, str]:
    """Extract the OBJECTID and field names from a config."""
    objectid = next(x["name"] for x in fields if x["type"] == OBJECTID)
    field_names = ",".join(
        [
            x["name"]
            for x in fields
            if x["type"] != OBJECTID
            and not x.get("virtual")
            and not x["name"].lower().startswith("objectid")
        ],
    )
    return objectid, field_names

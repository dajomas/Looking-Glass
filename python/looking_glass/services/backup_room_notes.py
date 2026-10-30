"""Schema-18 retained-note backup compatibility; never rewrite provenance."""
import math


def normalize_backup(data):
    """Normalize only recognized legacy documents parsed privately from JSON."""
    if (not isinstance(data, dict) or data.get("format") != "looking-glass-campaign"
            or type(data.get("version")) is not int or data["version"] != 1
            or type(data.get("schema")) is not int or data["schema"] not in (15, 16, 17, 18)):
        raise ValueError("Unsupported backup format or database schema")
    tables = data.get("tables")
    if not isinstance(tables, dict):
        raise ValueError("Invalid backup tables")
    maps = tables.get("maps")
    if not isinstance(maps, list) or len(maps) > 1000000:
        raise ValueError("Invalid backup maps")
    if data["schema"] in (15, 16, 17):
        if "room_note_archives" in tables:
            raise ValueError("Unexpected retained-note data in a legacy backup")
        for row in maps:
            if not isinstance(row, dict) or "room_notes_version" in row:
                raise ValueError("Unexpected note generation in a legacy backup")
            row["room_notes_version"] = 0
        tables["room_note_archives"] = []
    if data["schema"] in (15, 16):
        for table in ("double_reveal_maps", "double_reveal_rooms", "double_reveal_history"):
            if table in tables:
                raise ValueError("Unexpected double reveal data in a legacy backup")
            tables[table] = []
    return data


def validate_room_note_rows(tables):
    """Run after exact table/column/row-container checks, before replacement."""
    for row in tables["maps"]:
        if type(row["room_notes_version"]) is not int or row["room_notes_version"] < 0:
            raise ValueError("Invalid room-note generation")
    integer_fields = (
        "id", "map_id", "source_map_id", "source_campaign_id",
        "observed_walls_version", "source_width", "source_height", "source_revision",
    )
    text_fields = (
        "origin_uuid", "source_map_name", "source_campaign_name", "source_map_token",
        "area_key", "name", "markdown", "reason", "archived_at",
    )
    for row in tables["room_note_archives"]:
        if any(type(row[key]) is not int for key in integer_fields):
            raise ValueError("Invalid retained-note integer")
        if any(not isinstance(row[key], str) for key in text_fields):
            raise ValueError("Invalid retained-note text")
        for key in ("x", "y"):
            if type(row[key]) not in (int, float) or not math.isfinite(row[key]):
                raise ValueError("Invalid retained-note coordinate")
        if row["reason"] not in ("geometry_changed", "recovery_replacement"):
            raise ValueError("Invalid retained-note reason")
        # Historical identifiers/anchors need not reference current geometry.
        # Do not trim, truncate, normalize, deduplicate or remap source_* values.

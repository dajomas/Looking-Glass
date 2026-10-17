"""Persist boundary participation independently from source wall geometry."""
import json
from dataclasses import replace

WALL_TYPES = ("wall", "door", "secret", "window", "invisible", "ethereal")


def disabled_for_map(conn, row):
    saved = conn.execute("SELECT disabled_types FROM map_wall_type_settings WHERE map_id = ?", (row["id"],)).fetchone()
    raw = saved[0] if saved else row["disabled_wall_types"] if "disabled_wall_types" in row.keys() else "[]"
    disabled = json.loads(raw or "[]")
    if not isinstance(disabled, list) or any(k not in WALL_TYPES for k in disabled):
        raise ValueError("Invalid wall-type settings.")
    return sorted(set(disabled))


def save_disabled(conn, map_id, disabled):
    if any(k not in WALL_TYPES for k in disabled):
        raise ValueError("Unknown wall type.")
    raw = json.dumps(sorted(set(disabled)))
    conn.execute("INSERT INTO map_wall_type_settings(map_id, disabled_types) VALUES (?, ?) "
                 "ON CONFLICT(map_id) DO UPDATE SET disabled_types=excluded.disabled_types", (map_id, raw))
    columns = {r[1] for r in conn.execute("PRAGMA table_info(maps)")}
    if "disabled_wall_types" in columns:
        conn.execute("UPDATE maps SET disabled_wall_types = ? WHERE id = ?", (raw, map_id))
    conn.execute("UPDATE maps SET walls_version = walls_version + 1, fog_version = fog_version + 1 WHERE id = ?", (map_id,))


def boundary_segments(segments, disabled):
    return [replace(s, blocks=False) if s.kind in disabled else s for s in segments]

"""Evaluate saved reveal operations, not merely their count or presence."""
import json

from .wall_model import FogOp


def checkpoint_operations(conn, map_id):
    row = conn.execute("SELECT operations FROM map_fog_snapshots WHERE map_id = ?", (map_id,)).fetchone()
    if row is None:
        return []
    data = json.loads(row["operations"])
    if not isinstance(data, list):
        raise ValueError("Invalid saved reveal checkpoint.")
    return [FogOp(item["op"], item.get("x"), item.get("y")) for item in data]


def has_restorable_reveals(engine, spec, segments, operations):
    if not operations:
        return False
    area = engine.area_map(spec, segments)
    return bool(engine.revealed_labels(area, operations))

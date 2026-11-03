"""Transactional data hooks for historical migrations."""
import json
import sqlite3


def _initialize_ordered_fog_snapshots(conn: sqlite3.Connection) -> None:
    operations_by_map: dict[int, list[dict]] = {}
    for row in conn.execute("SELECT map_id, op, x, y FROM fog_ops ORDER BY map_id, id"):
        operations_by_map.setdefault(row["map_id"], []).append(
            {"op": row["op"], "x": row["x"], "y": row["y"]}
        )
    conn.executemany(
        "UPDATE map_fog_snapshots SET operations = ? WHERE map_id = ?",
        [(json.dumps(ops, separators=(",", ":")), mid)
         for mid, ops in operations_by_map.items()],
    )


def apply_migration(conn: sqlite3.Connection, version: int, script: str) -> None:
    """Apply one pending migration; version 3's data hook commits atomically."""
    if version != 3:
        conn.executescript(
            "BEGIN;" + script
            + f"; INSERT INTO schema_version VALUES ({version}); COMMIT;"
        )
        return
    try:
        conn.executescript("BEGIN;" + script)
        _initialize_ordered_fog_snapshots(conn)
        conn.execute("INSERT INTO schema_version VALUES (?)", (version,))
        conn.commit()
    except BaseException:
        conn.rollback()
        raise

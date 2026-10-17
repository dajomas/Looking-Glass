import sqlite3
from collections.abc import Iterable

from ..services.wall_model import WallSegment


def list_for_map(conn: sqlite3.Connection, map_id: int) -> list[WallSegment]:
    rows = conn.execute("SELECT x1, y1, x2, y2, kind, blocks FROM walls WHERE map_id = ? ORDER BY id",
                        (map_id,)).fetchall()
    return [WallSegment(r["x1"], r["y1"], r["x2"], r["y2"], r["kind"], bool(r["blocks"])) for r in rows]


def replace(conn: sqlite3.Connection, map_id: int, segments: Iterable[WallSegment]) -> int:
    conn.execute("DELETE FROM walls WHERE map_id = ?", (map_id,))
    rows = [(map_id, s.x1, s.y1, s.x2, s.y2, s.kind, int(s.blocks)) for s in segments]
    conn.executemany("INSERT INTO walls (map_id, x1, y1, x2, y2, kind, blocks) VALUES (?, ?, ?, ?, ?, ?, ?)", rows)
    return len(rows)


def clear(conn: sqlite3.Connection, map_id: int) -> None:
    conn.execute("DELETE FROM walls WHERE map_id = ?", (map_id,))

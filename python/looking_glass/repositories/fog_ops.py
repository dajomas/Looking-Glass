import sqlite3

from ..services.wall_model import FogOp


def list_for_map(conn: sqlite3.Connection, map_id: int) -> list[FogOp]:
    rows = conn.execute("SELECT op, x, y FROM fog_ops WHERE map_id = ? ORDER BY id", (map_id,)).fetchall()
    return [FogOp(r["op"], r["x"], r["y"]) for r in rows]


def count(conn: sqlite3.Connection, map_id: int) -> int:
    return conn.execute("SELECT COUNT(*) FROM fog_ops WHERE map_id = ?", (map_id,)).fetchone()[0]


def add(conn: sqlite3.Connection, map_id: int, op: str, x: float | None, y: float | None, user_id: int) -> None:
    conn.execute("INSERT INTO fog_ops (map_id, op, x, y, created_by) VALUES (?, ?, ?, ?, ?)",
                 (map_id, op, x, y, user_id))


def undo(conn: sqlite3.Connection, map_id: int) -> bool:
    row = conn.execute("SELECT MAX(id) FROM fog_ops WHERE map_id = ?", (map_id,)).fetchone()
    if row[0] is None:
        return False
    conn.execute("DELETE FROM fog_ops WHERE id = ?", (row[0],))
    return True


def clear(conn: sqlite3.Connection, map_id: int) -> None:
    conn.execute("DELETE FROM fog_ops WHERE map_id = ?", (map_id,))

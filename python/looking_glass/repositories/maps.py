import sqlite3


def get(conn: sqlite3.Connection, map_id: int) -> sqlite3.Row | None:
    return conn.execute(
        """SELECT m.*, (SELECT COUNT(*) FROM walls w WHERE w.map_id = m.id) AS wall_count
             FROM maps m WHERE m.id = ?""", (map_id,)).fetchone()


def list_for_campaign(conn: sqlite3.Connection, campaign_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        """SELECT m.*, (SELECT COUNT(*) FROM walls w WHERE w.map_id = m.id) AS wall_count
             FROM maps m WHERE m.campaign_id = ? ORDER BY m.sort_order, m.id""", (campaign_id,)).fetchall()


def create(conn: sqlite3.Connection, campaign_id: int, name: str, image_file: str, width: int, height: int,
           doors_block: bool) -> int:
    order = conn.execute("SELECT COALESCE(MAX(sort_order), 0) + 1 FROM maps WHERE campaign_id = ?",
                         (campaign_id,)).fetchone()[0]
    return conn.execute(
        """INSERT INTO maps (campaign_id, name, image_file, width, height, sort_order, doors_block)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (campaign_id, name.strip(), image_file, width, height, order, int(doors_block)),
    ).lastrowid


def rename(conn: sqlite3.Connection, map_id: int, name: str) -> None:
    conn.execute("UPDATE maps SET name = ? WHERE id = ?", (name.strip(), map_id))


def replace_image(conn: sqlite3.Connection, map_id: int, image_file: str, width: int, height: int) -> None:
    conn.execute("""UPDATE maps SET image_file = ?, width = ?, height = ?,
                    walls_version = walls_version + 1, fog_version = fog_version + 1 WHERE id = ?""",
                 (image_file, width, height, map_id))


def move(conn: sqlite3.Connection, map_id: int, direction: int) -> None:
    """Swap sort order with the neighbouring map (direction -1 = up, +1 = down)."""
    m = get(conn, map_id)
    if not m:
        return
    siblings = list_for_campaign(conn, m["campaign_id"])
    ids = [s["id"] for s in siblings]
    i = ids.index(map_id)
    j = i + direction
    if 0 <= j < len(ids):
        ids[i], ids[j] = ids[j], ids[i]
        for order, mid in enumerate(ids, start=1):
            conn.execute("UPDATE maps SET sort_order = ? WHERE id = ?", (order, mid))


def set_calibration(conn: sqlite3.Connection, map_id: int, offset_x: float, offset_y: float,
                    scale_x: float, scale_y: float, doors_block: bool) -> None:
    conn.execute(
        """UPDATE maps SET wall_offset_x = ?, wall_offset_y = ?, wall_scale_x = ?, wall_scale_y = ?,
                  doors_block = ?, walls_version = walls_version + 1, fog_version = fog_version + 1
            WHERE id = ?""",
        (offset_x, offset_y, scale_x, scale_y, int(doors_block), map_id),
    )


def set_walls_source(conn: sqlite3.Connection, map_id: int, source: str) -> None:
    conn.execute("""UPDATE maps SET walls_source = ?, walls_version = walls_version + 1,
                    fog_version = fog_version + 1 WHERE id = ?""", (source, map_id))


def bump_fog(conn: sqlite3.Connection, map_id: int) -> int:
    conn.execute("UPDATE maps SET fog_version = fog_version + 1 WHERE id = ?", (map_id,))
    return conn.execute("SELECT fog_version FROM maps WHERE id = ?", (map_id,)).fetchone()[0]


def delete(conn: sqlite3.Connection, map_id: int) -> None:
    conn.execute("UPDATE campaigns SET active_map_id = NULL WHERE active_map_id = ?", (map_id,))
    conn.execute("DELETE FROM maps WHERE id = ?", (map_id,))

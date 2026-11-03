import sqlite3
from typing import Any, Mapping

from ..rbac import Role, role_of

_SELECT = """SELECT c.*, u.username AS owner_name,
                    (SELECT COUNT(*) FROM maps m WHERE m.campaign_id = c.id) AS map_count,
                    (SELECT COUNT(*) FROM campaign_viewers v WHERE v.campaign_id = c.id) AS viewer_count
               FROM campaigns c LEFT JOIN users u ON u.id = c.owner_id"""


def get(conn: sqlite3.Connection, campaign_id: int) -> sqlite3.Row | None:
    return conn.execute(f"{_SELECT} WHERE c.id = ?", (campaign_id,)).fetchone()


def list_manageable(conn: sqlite3.Connection, user: Mapping[str, Any]) -> list[sqlite3.Row]:
    if role_of(user) is Role.SUPERADMIN:
        return conn.execute(f"{_SELECT} ORDER BY c.name").fetchall()
    return conn.execute(f"{_SELECT} WHERE c.owner_id = ? ORDER BY c.name", (user["id"],)).fetchall()


def list_viewable(conn: sqlite3.Connection, user: Mapping[str, Any]) -> list[sqlite3.Row]:
    if role_of(user) is Role.SUPERADMIN:
        return conn.execute(f"{_SELECT} ORDER BY c.name").fetchall()
    return conn.execute(
        f"""{_SELECT} WHERE c.owner_id = ?
               OR c.id IN (SELECT campaign_id FROM campaign_viewers WHERE user_id = ?)
            ORDER BY c.name""",
        (user["id"], user["id"]),
    ).fetchall()


def create(conn: sqlite3.Connection, name: str, description: str, owner_id: int) -> int:
    return conn.execute("INSERT INTO campaigns (name, description, owner_id) VALUES (?, ?, ?)",
                        (name.strip(), description.strip(), owner_id)).lastrowid


def update(conn: sqlite3.Connection, campaign_id: int, name: str, description: str,
           owner_id: int | None = None) -> None:
    if owner_id is None:
        conn.execute("UPDATE campaigns SET name = ?, description = ? WHERE id = ?",
                     (name.strip(), description.strip(), campaign_id))
    else:
        conn.execute("UPDATE campaigns SET name = ?, description = ?, owner_id = ? WHERE id = ?",
                     (name.strip(), description.strip(), owner_id, campaign_id))


def set_active_map(conn: sqlite3.Connection, campaign_id: int, map_id: int | None) -> None:
    conn.execute("UPDATE campaigns SET active_map_id = ? WHERE id = ?", (map_id, campaign_id))


def delete(conn: sqlite3.Connection, campaign_id: int) -> None:
    conn.execute("DELETE FROM campaigns WHERE id = ?", (campaign_id,))


# --- viewer assignments ------------------------------------------------------
def list_viewers(conn: sqlite3.Connection, campaign_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        """SELECT u.id, u.username, u.display_name, u.role, u.active, v.added_at
             FROM campaign_viewers v JOIN users u ON u.id = v.user_id
            WHERE v.campaign_id = ? ORDER BY u.username""",
        (campaign_id,),
    ).fetchall()


def list_assignable_users(conn: sqlite3.Connection, campaign_id: int, owner_id: int | None) -> list[sqlite3.Row]:
    return conn.execute(
        """SELECT id, username, display_name, role FROM users
            WHERE active = 1 AND id IS NOT ?
              AND id NOT IN (SELECT user_id FROM campaign_viewers WHERE campaign_id = ?)
            ORDER BY role DESC, username""",
        (owner_id, campaign_id),
    ).fetchall()


def add_viewer(conn: sqlite3.Connection, campaign_id: int, user_id: int, added_by: int) -> None:
    conn.execute("INSERT OR IGNORE INTO campaign_viewers (campaign_id, user_id, added_by) VALUES (?, ?, ?)",
                 (campaign_id, user_id, added_by))


def remove_viewer(conn: sqlite3.Connection, campaign_id: int, user_id: int) -> None:
    conn.execute("DELETE FROM campaign_viewers WHERE campaign_id = ? AND user_id = ?", (campaign_id, user_id))

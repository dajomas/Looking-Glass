import sqlite3

from ..rbac import Role
from ..security import hash_password

_COLS = "id, username, display_name, role, active, must_change_password, created_by, created_at"


def get(conn: sqlite3.Connection, user_id: int) -> sqlite3.Row | None:
    return conn.execute(f"SELECT {_COLS} FROM users WHERE id = ?", (user_id,)).fetchone()


def get_with_hash(conn: sqlite3.Connection, username: str) -> sqlite3.Row | None:
    return conn.execute(f"SELECT {_COLS}, password_hash FROM users WHERE username = ?", (username,)).fetchone()


def list_all(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(f"SELECT {_COLS} FROM users ORDER BY role, username").fetchall()


def list_by_role(conn: sqlite3.Connection, role: Role) -> list[sqlite3.Row]:
    return conn.execute(f"SELECT {_COLS} FROM users WHERE role = ? ORDER BY username", (role.value,)).fetchall()


def count_superadmins(conn: sqlite3.Connection, active_only: bool = True) -> int:
    sql = "SELECT COUNT(*) FROM users WHERE role = 'superadmin'" + (" AND active = 1" if active_only else "")
    return conn.execute(sql).fetchone()[0]


def create(conn: sqlite3.Connection, username: str, password: str, role: Role, display_name: str = "",
           created_by: int | None = None, must_change_password: bool = False) -> int:
    cur = conn.execute(
        "INSERT INTO users (username, display_name, password_hash, role, must_change_password, created_by)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        (username.strip(), display_name.strip(), hash_password(password), role.value,
         int(must_change_password), created_by),
    )
    return cur.lastrowid


def update(conn: sqlite3.Connection, user_id: int, *, display_name: str | None = None,
           role: Role | None = None, active: bool | None = None) -> None:
    fields, params = [], []
    if display_name is not None:
        fields.append("display_name = ?"); params.append(display_name.strip())
    if role is not None:
        fields.append("role = ?"); params.append(role.value)
    if active is not None:
        fields.append("active = ?"); params.append(int(active))
    if fields:
        conn.execute(f"UPDATE users SET {', '.join(fields)} WHERE id = ?", (*params, user_id))


def set_password(conn: sqlite3.Connection, user_id: int, password: str, must_change: bool = False) -> None:
    conn.execute("UPDATE users SET password_hash = ?, must_change_password = ? WHERE id = ?",
                 (hash_password(password), int(must_change), user_id))


def delete(conn: sqlite3.Connection, user_id: int) -> None:
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))

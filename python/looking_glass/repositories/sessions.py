import sqlite3
import time

from ..security import new_token, token_hash


def create(conn: sqlite3.Connection, user_id: int, entry: str, ttl_seconds: int) -> tuple[str, str]:
    """Create a session; returns (raw_token, csrf_token). Only the hash is stored."""
    token, csrf = new_token(), new_token()
    conn.execute(
        "INSERT INTO sessions (token_hash, user_id, entry, csrf_token, expires_at) VALUES (?, ?, ?, ?, ?)",
        (token_hash(token), user_id, entry, csrf, int(time.time()) + ttl_seconds),
    )
    return token, csrf


def lookup(conn: sqlite3.Connection, token: str, entry: str) -> sqlite3.Row | None:
    """Return the joined session+user row for a valid, unexpired token on this entry point."""
    return conn.execute(
        """SELECT s.csrf_token, s.expires_at, u.id, u.username, u.display_name, u.role, u.active,
                  u.must_change_password
             FROM sessions s JOIN users u ON u.id = s.user_id
            WHERE s.token_hash = ? AND s.entry = ? AND s.expires_at > ?""",
        (token_hash(token), entry, int(time.time())),
    ).fetchone()


def delete(conn: sqlite3.Connection, token: str) -> None:
    conn.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash(token),))


def delete_for_user(conn: sqlite3.Connection, user_id: int, keep_token: str | None = None) -> None:
    if keep_token:
        conn.execute("DELETE FROM sessions WHERE user_id = ? AND token_hash != ?", (user_id, token_hash(keep_token)))
    else:
        conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))


def purge_expired(conn: sqlite3.Connection) -> int:
    return conn.execute("DELETE FROM sessions WHERE expires_at <= ?", (int(time.time()),)).rowcount

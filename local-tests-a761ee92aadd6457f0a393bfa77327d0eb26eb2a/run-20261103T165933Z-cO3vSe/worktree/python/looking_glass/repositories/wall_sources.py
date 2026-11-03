"""Immutable campaign-scoped source uploads; no map depends on source lifetime."""

import hashlib
import sqlite3


def save(conn: sqlite3.Connection, campaign_id: int, filename: str, raw: bytes, scene_count: int):
    digest = hashlib.sha256(raw).hexdigest()
    filename = filename.replace("\\", "/").rsplit("/", 1)[-1][:255] or "walls"
    conn.execute(
        "INSERT INTO wall_sources (campaign_id, filename, sha256, raw, scene_count) "
        "VALUES (?, ?, ?, ?, ?) ON CONFLICT(campaign_id, sha256) DO NOTHING",
        (campaign_id, filename, digest, raw, scene_count),
    )
    return conn.execute("SELECT * FROM wall_sources WHERE campaign_id = ? AND sha256 = ?",
                        (campaign_id, digest)).fetchone()


def list_for_campaign(conn: sqlite3.Connection, campaign_id: int):
    return conn.execute(
        "SELECT id, filename, scene_count, created_at FROM wall_sources "
        "WHERE campaign_id = ? ORDER BY filename COLLATE NOCASE, id", (campaign_id,)
    ).fetchall()


def get(conn: sqlite3.Connection, campaign_id: int, source_id: int):
    return conn.execute("SELECT * FROM wall_sources WHERE campaign_id = ? AND id = ?",
                        (campaign_id, source_id)).fetchone()


def delete(conn: sqlite3.Connection, campaign_id: int, source_id: int):
    conn.execute("DELETE FROM wall_sources WHERE campaign_id = ? AND id = ?", (campaign_id, source_id))

"""Explicit room-note recovery. Callers own authorization and transaction."""

from . import room_notes


class ArchiveNotFound(LookupError):
    pass


class RecoveryConflict(ValueError):
    pass


def list_archives(conn, map_id, limit=50, before_id=None):
    """Return a bounded, newest-first page of retained assignments."""
    if not conn.in_transaction:
        raise RuntimeError("Archive listing requires a transaction.")
    if not 1 <= limit <= 200:
        raise ValueError("Archive page size must be between 1 and 200.")
    if before_id is not None and before_id <= 0:
        raise ValueError("Archive cursor must be positive.")
    rows = conn.execute(
        """SELECT * FROM room_note_archives
        WHERE map_id=? AND (? IS NULL OR id<?)
        ORDER BY id DESC LIMIT ?""",
        (map_id, before_id, before_id, limit + 1),
    ).fetchall()
    page = rows[:limit]
    next_before_id = page[-1]["id"] if len(rows) > limit else None
    return {"archives": [dict(row) for row in page],
            "next_before_id": next_before_id}


def recover_archive(conn, map_id, archive_id, area_key, x, y, revision, overwrite=False):
    """Copy retained content into an explicitly validated current target.

    Caller must hold a write transaction, authorize management, and validate
    map incarnation, geometry, generation, target area identity and revision
    in this transaction. Archives are retained after recovery.
    """
    if not conn.in_transaction:
        raise RuntimeError("Recovery requires an active transaction.")
    conn.execute("SAVEPOINT room_note_recovery")
    try:
        archive = conn.execute(
            "SELECT * FROM room_note_archives WHERE map_id=? AND id=?",
            (map_id, archive_id),
        ).fetchone()
        if archive is None:
            raise ArchiveNotFound("Retained room note not found on this map.")
        target = conn.execute(
            "SELECT name,markdown,revision FROM room_notes WHERE map_id=? AND area_key=?",
            (map_id, area_key),
        ).fetchone()
        current_revision = target["revision"] if target else 0
        if current_revision != revision:
            raise RecoveryConflict("Target notes changed. Select the room again.")
        # Whitespace is content too: do not discard it silently.
        target_has_content = target is not None and bool(target["name"] or target["markdown"])
        if target_has_content:
            if not overwrite:
                raise RecoveryConflict(
                    "The selected room already has a name or notes. "
                    "Confirm replacement before recovering."
                )
            room_notes.archive_assignment(conn, map_id, area_key, "recovery_replacement")
        result = conn.execute(
            """INSERT INTO room_notes(map_id,area_key,x,y,name,markdown)
            VALUES(?,?,?,?,?,?)
            ON CONFLICT(map_id,area_key) DO UPDATE SET
                x=excluded.x,y=excluded.y,name=excluded.name,
                markdown=excluded.markdown,revision=room_notes.revision+1
            WHERE room_notes.revision=?""",
            (map_id, area_key, x, y, archive["name"], archive["markdown"], revision),
        )
        if result.rowcount != 1:
            raise RecoveryConflict(
                "Target notes changed while recovering. Select the room again."
            )
        conn.execute("RELEASE room_note_recovery")
    except BaseException:
        if conn.in_transaction:
            conn.execute("ROLLBACK TO room_note_recovery")
            conn.execute("RELEASE room_note_recovery")
        raise

"""Conservative geometry identity and safe, admin-only Markdown rendering."""
import hashlib
import uuid
import numpy as np
import mistune
import bleach

_markdown = mistune.create_markdown(escape=True, plugins=["table", "strikethrough"])

def render(text):
    return bleach.clean(_markdown(text), tags={
        "p", "br", "hr", "h1", "h2", "h3", "h4", "h5", "h6", "strong", "em",
        "del", "blockquote", "ul", "ol", "li", "pre", "code", "a",
        "table", "thead", "tbody", "tr", "th", "td"},
        attributes={"a": ["href", "title"]}, protocols={"https", "http", "mailto"}, strip=True)

def area_key(area, label, width, height):
    cached = area.region_signatures.get(("notes", label, width, height))
    if cached:
        return cached
    mask = area.labels == label
    key = hashlib.sha256(repr((width, height, area.shape, area.scale)).encode()
                         + np.packbits(mask).tobytes()).hexdigest()
    area.region_signatures[("notes", label, width, height)] = key
    return key

def payload(conn, map_id, key, revealed):
    row = conn.execute("SELECT * FROM room_notes WHERE map_id=? AND area_key=?", (map_id, key)).fetchone()
    return {"area_key": key, "revealed": revealed, "name": row["name"] if row else "",
            "markdown": row["markdown"] if row else "", "revision": row["revision"] if row else 0,
            "html": render(row["markdown"]) if row else ""}


def edit_mask_png(area, label):
    """Independent admin decoration; never updates fog masks or operations."""
    import io
    from PIL import Image
    from scipy import ndimage
    mask = area.labels == label
    edge = mask & ~ndimage.binary_erosion(mask, iterations=2, border_value=0)
    rgba = np.zeros((*mask.shape, 4), dtype=np.uint8)
    rgba[mask] = (255, 193, 7, 75)
    rgba[edge] = (255, 193, 7, 245)
    out = io.BytesIO()
    Image.fromarray(rgba).save(out, "PNG")
    return out.getvalue()


def name_status_png(area, rows, width, height):
    """Color current areas by saved, geometry-matched names, independent of fog."""
    import io
    from PIL import Image
    named = set()
    h, w = area.labels.shape
    for row in rows:
        if not row["name"].strip() or not (0 <= row["x"] < width and 0 <= row["y"] < height):
            continue
        px, py = int(row["x"] * area.scale), int(row["y"] * area.scale)
        if px >= w or py >= h:
            continue
        label = int(area.labels[py, px])
        if label and area_key(area, label, width, height) == row["area_key"]:
            named.add(label)
    palette = np.zeros((area.count + 1, 4), dtype=np.uint8)
    palette[1:] = (231, 76, 60, 90)
    for label in named:
        palette[label] = (46, 204, 113, 90)
    rgba = palette[area.labels]
    out = io.BytesIO()
    Image.fromarray(rgba).save(out, "PNG")
    return out.getvalue(), len(named), area.count - len(named)


def _begin_note_transaction(conn):
    """Start a write transaction unless the caller already owns one.

    Never commit here: the caller must commit or roll back reconciliation
    together with its surrounding operation.
    """
    if not conn.in_transaction:
        conn.execute("BEGIN IMMEDIATE")


def archive_assignment(conn, map_id, key, reason):
    """Retain one complete active assignment without modifying it.

    The caller must hold a transaction and protect any subsequent replacement
    or detachment with that same transaction/savepoint.

    Historical provenance describes the state observed during archival.
    """
    if not conn.in_transaction:
        raise RuntimeError("Archiving requires an active transaction.")

    result = conn.execute(
        """
        INSERT INTO room_note_archives (
            map_id,
            origin_uuid,
            source_map_id,
            source_campaign_id,
            source_map_name,
            source_campaign_name,
            source_map_token,
            observed_walls_version,
            source_width,
            source_height,
            area_key,
            x,
            y,
            name,
            markdown,
            source_revision,
            reason
        )
        SELECT
            n.map_id,
            ?,
            m.id,
            m.campaign_id,
            m.name,
            c.name,
            m.cache_token,
            m.walls_version,
            m.width,
            m.height,
            n.area_key,
            n.x,
            n.y,
            n.name,
            n.markdown,
            n.revision,
            ?
        FROM room_notes AS n
        JOIN maps AS m ON m.id = n.map_id
        JOIN campaigns AS c ON c.id = m.campaign_id
        WHERE n.map_id = ? AND n.area_key = ?
        """,
        (uuid.uuid4().hex, reason, map_id, key),
    )

    if result.rowcount != 1:
        raise RuntimeError("Room assignment changed while archiving.")

    return result.lastrowid


def remove_stale(conn, map_id, area, width, height):
    """Archive and detach assignments whose anchored geometry changed.

    The supplied area map must represent the caller's current effective
    boundaries. Production callers should use reconcile_map(), which loads
    geometry inside the transaction.

    Imported libraries, unaffected rooms and other maps remain unchanged.
    Never snap anchors or automatically reattach archived content.
    """
    _begin_note_transaction(conn)

    conn.execute("SAVEPOINT room_note_reconcile")
    try:
        stale = []
        rows = conn.execute(
            """
            SELECT area_key, x, y
            FROM room_notes
            WHERE map_id = ?
            ORDER BY area_key
            """,
            (map_id,),
        ).fetchall()

        for row in rows:
            x, y = row["x"], row["y"]
            label = 0

            if 0 <= x < width and 0 <= y < height:
                px = int(x * area.scale)
                py = int(y * area.scale)

                if (
                    0 <= py < area.shape[0]
                    and 0 <= px < area.shape[1]
                ):
                    label = int(area.labels[py, px])

            if (
                not label
                or area_key(area, label, width, height)
                != row["area_key"]
            ):
                stale.append(row["area_key"])

        # Retain every affected assignment before detaching any of them.
        # Do not use INSERT OR IGNORE: an archive failure must stop deletion.
        for key in stale:
            archive_assignment(
                conn, map_id, key, "geometry_changed"
            )

        for key in stale:
            deleted = conn.execute(
                """
                DELETE FROM room_notes
                WHERE map_id = ? AND area_key = ?
                """,
                (map_id, key),
            ).rowcount

            if deleted != 1:
                raise RuntimeError(
                    "Room assignment changed while detaching."
                )

        conn.execute("RELEASE room_note_reconcile")
        return len(stale)

    except BaseException:
        # Some SQLite errors can abort the entire transaction themselves.
        # In that case its savepoint no longer exists and nothing remains
        # to roll back locally.
        if conn.in_transaction:
            conn.execute("ROLLBACK TO room_note_reconcile")
            conn.execute("RELEASE room_note_reconcile")
        raise


def reconcile_map(ctx, conn, map_id):
    """Reconcile notes against current effective boundaries.

    Start the transaction before querying notes or loading geometry.
    Include calibration, runtime boundaries and wall-type settings through
    the existing fog_inputs()/area_map() path.
    """
    _begin_note_transaction(conn)

    has_notes = conn.execute(
        "SELECT 1 FROM room_notes WHERE map_id = ? LIMIT 1",
        (map_id,),
    ).fetchone()

    if not has_notes:
        return 0

    from ..web.access import fog_inputs

    spec, segments, _ = fog_inputs(ctx, conn, map_id)
    area = ctx.fog.area_map(spec, segments)

    return remove_stale(
        conn,
        map_id,
        area,
        spec.width,
        spec.height,
    )

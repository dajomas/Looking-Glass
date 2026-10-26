"""Optional artwork variants. Geometry identities fail closed; callers own transactions."""
import math
from PIL import Image
import numpy as np
from .room_notes import area_key

TABLES = ("double_reveal_maps", "double_reveal_rooms", "double_reveal_history")


def locate(area, spec, x, y):
    if not (math.isfinite(x) and math.isfinite(y) and 0 <= x < spec.width and 0 <= y < spec.height):
        raise ValueError("Select a point inside the map.")
    label = int(area.labels[int(y * area.scale), int(x * area.scale)])
    if not label:
        raise ValueError("Select inside a room, not on a wall.")
    return label, area_key(area, label, spec.width, spec.height)


def matches(area, spec, row):
    try:
        label, key = locate(area, spec, row["x"], row["y"])
        return label if key == row["area_key"] else 0
    except ValueError:
        return 0


def inputs(conn, map_id, maps_dir):
    image = conn.execute("SELECT * FROM double_reveal_maps WHERE map_id=?", (map_id,)).fetchone()
    rooms = tuple((r["area_key"], r["x"], r["y"], r["true_active"]) for r in conn.execute(
        "SELECT * FROM double_reveal_rooms WHERE map_id=? ORDER BY area_key", (map_id,)))
    return (maps_dir / image["image_file"] if image else None), rooms


def composite(engine, spec, segments, base):
    if spec.alternate_image_path is None or not any(r[3] for r in spec.double_reveal_rooms):
        return base
    area = engine.area_map(spec, segments)
    labels = [matches(area, spec, dict(area_key=key, x=x, y=y))
              for key, x, y, active in spec.double_reveal_rooms if active]
    labels = [label for label in labels if label]
    if not labels:
        return base
    with Image.open(spec.alternate_image_path) as src:
        if src.size != (spec.width, spec.height):
            raise ValueError("Alternate image dimensions no longer match.")
        alternate = src.convert("RGB").resize(base.size, Image.Resampling.LANCZOS)
    # Artwork stays inside room interiors; never dilate truth into neighbours.
    mask = Image.fromarray((np.isin(area.labels, labels) * 255).astype(np.uint8)).resize(base.size, Image.Resampling.NEAREST)
    return Image.composite(alternate, base, mask)


def listing(conn, engine, spec, segments, ops):
    image = conn.execute("SELECT revision FROM double_reveal_maps WHERE map_id=?", (spec.id,)).fetchone()
    area = engine.area_map(spec, segments)
    revealed = engine.revealed_labels(area, ops)
    result = []
    for row in conn.execute("""SELECT r.*, n.name, m.name AS destination_name
        FROM double_reveal_rooms r LEFT JOIN room_notes n ON n.map_id=r.map_id AND n.area_key=r.area_key
        LEFT JOIN maps m ON m.id=r.destination_map_id WHERE r.map_id=? ORDER BY r.area_key""", (spec.id,)):
        label = matches(area, spec, row)
        result.append({**dict(row), "valid_geometry": bool(label), "revealed": bool(label and label in revealed)})
    return dict(image_revision=image[0] if image else 0, rooms=result,
        can_undo=bool(conn.execute("SELECT 1 FROM double_reveal_history WHERE map_id=? LIMIT 1", (spec.id,)).fetchone()))


def configure(conn, spec, area, x, y, revision, enabled, destination):
    _, key = locate(area, spec, x, y)
    row = conn.execute("SELECT * FROM double_reveal_rooms WHERE map_id=? AND area_key=?", (spec.id, key)).fetchone()
    if revision != (row["revision"] if row else 0):
        raise ValueError("Room changed. Select it again before saving.")
    if destination is not None:
        own = conn.execute("SELECT campaign_id FROM maps WHERE id=?", (spec.id,)).fetchone()[0]
        target = conn.execute("SELECT campaign_id FROM maps WHERE id=?", (destination,)).fetchone()
        if target is None or target[0] != own or destination == spec.id:
            raise ValueError("Choose another map in this campaign.")
    if not enabled:
        conn.execute("DELETE FROM double_reveal_rooms WHERE map_id=? AND area_key=?", (spec.id, key))
    else:
        if not conn.execute("SELECT 1 FROM double_reveal_maps WHERE map_id=?", (spec.id,)).fetchone():
            raise ValueError("Upload an alternate full-map image first.")
        conn.execute("""INSERT INTO double_reveal_rooms(map_id,area_key,x,y,destination_map_id)
            VALUES(?,?,?,?,?) ON CONFLICT(map_id,area_key) DO UPDATE SET
            destination_map_id=excluded.destination_map_id,revision=double_reveal_rooms.revision+1""",
            (spec.id, key, x, y, destination))
    return key


def change(conn, spec, area, key, revision, true_active):
    row = conn.execute("SELECT * FROM double_reveal_rooms WHERE map_id=? AND area_key=?", (spec.id, key)).fetchone()
    if row is None or row["revision"] != revision:
        raise ValueError("Room changed. Select it again.")
    if not matches(area, spec, row):
        raise ValueError("Room geometry changed. Reconfigure this room before revealing it.")
    if not conn.execute("SELECT 1 FROM double_reveal_maps WHERE map_id=?", (spec.id,)).fetchone():
        raise ValueError("Alternate image is missing.")
    if bool(row["true_active"]) == true_active:
        return False
    conn.execute("INSERT INTO double_reveal_history(map_id,area_key,before_state,after_state) VALUES(?,?,?,?)",
        (spec.id, key, row["true_active"], int(true_active)))
    conn.execute("UPDATE double_reveal_rooms SET true_active=?,revision=revision+1 WHERE map_id=? AND area_key=?",
        (int(true_active), spec.id, key))
    return True


def undo(conn, spec, area):
    row = conn.execute("SELECT * FROM double_reveal_history WHERE map_id=? ORDER BY id DESC LIMIT 1", (spec.id,)).fetchone()
    if row is None:
        raise ValueError("No appearance change to undo.")
    room = conn.execute("SELECT * FROM double_reveal_rooms WHERE map_id=? AND area_key=?", (spec.id, row["area_key"])).fetchone()
    if not matches(area, spec, room):
        raise ValueError("Last changed room geometry no longer matches; remove its stale configuration first.")
    conn.execute("UPDATE double_reveal_rooms SET true_active=?,revision=revision+1 WHERE map_id=? AND area_key=?",
        (row["before_state"], spec.id, row["area_key"]))
    conn.execute("DELETE FROM double_reveal_history WHERE id=?", (row["id"],))


def navigate(conn, engine, spec, segments, ops, key, revision, expected_active):
    """Preserve destination play state verbatim. Caller authorizes source and locks DB."""
    from .map_display import checkpoint
    campaign = conn.execute("SELECT c.* FROM campaigns c JOIN maps m ON m.campaign_id=c.id WHERE m.id=?", (spec.id,)).fetchone()
    if expected_active != spec.id or campaign["active_map_id"] != expected_active:
        raise ValueError("Show the source map to players first; the active map may have changed.")
    row = conn.execute("SELECT * FROM double_reveal_rooms WHERE map_id=? AND area_key=?", (spec.id, key)).fetchone()
    if row is None or row["revision"] != revision or not row["true_active"]:
        raise ValueError("Reveal the true appearance before using this link.")
    area = engine.area_map(spec, segments)
    label = matches(area, spec, row)
    if not label or label not in engine.revealed_labels(area, ops):
        raise ValueError("The source room must be visible and its geometry unchanged.")
    target = row["destination_map_id"]
    destination = conn.execute("SELECT campaign_id FROM maps WHERE id=?", (target,)).fetchone()
    if destination is None or destination[0] != campaign["id"] or target == spec.id:
        raise ValueError("Destination map is missing or invalid.")
    checkpoint(conn, spec.id)
    checkpoint(conn, target)
    conn.execute("UPDATE campaigns SET active_map_id=?,session_version=session_version+1 WHERE id=?", (target, campaign["id"]))
    return target, campaign["id"]

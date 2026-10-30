"""Clean authored-content copies. Caller owns transaction and file rollback."""
import uuid
from . import images
from ..repositories import campaigns

AUTHORED = ("walls", "map_wall_type_settings", "room_notes", "imported_room_notes", "room_note_archives", "map_transitions", "double_reveal_maps", "double_reveal_rooms")


def _insert(conn, table, row):
    keys = list(row)
    return conn.execute(f'INSERT INTO {table} ({",".join(keys)}) VALUES ({",".join("?" for _ in keys)})',
                        [row[k] for k in keys]).lastrowid


def duplicate(conn, source_id, maps_dir, created_files, name, owner_id, map_id=None):
    """Copy a campaign, or one map into its existing campaign; never publish it.

    BEGIN IMMEDIATE and authorization are required from the caller. Single-map
    external destinations are detached, never left pointing into the source.
    """
    name = name.strip()
    if not 1 <= len(name) <= 120:
        raise ValueError("Name must contain 1–120 characters")
    source = conn.execute("SELECT * FROM campaigns WHERE id=?", (source_id,)).fetchone()
    if source is None:
        raise ValueError("Unknown campaign")
    selected = [dict(r) for r in conn.execute("SELECT * FROM maps WHERE campaign_id=? ORDER BY sort_order,id", (source_id,))
                if map_id is None or r["id"] == map_id]
    if map_id is not None and not selected:
        raise ValueError("Map does not belong to campaign")
    target = source_id if map_id is not None else campaigns.create(conn, name, source["description"], owner_id)
    mapping = {}
    endpoints = []
    double_links = []
    for original in selected:
        row = dict(original)
        old = row.pop("id")
        path = (maps_dir / row["image_file"]).resolve()
        if maps_dir.resolve() not in path.parents:
            raise ValueError("Invalid stored image path")
        stored = images.store_map_image(path.read_bytes(), maps_dir, target)
        created_files.append(stored.relative_path)
        if (stored.width, stored.height) != (row["width"], row["height"]):
            raise ValueError("Image dimensions do not match")
        row.update(campaign_id=target, image_file=stored.relative_path, cache_token=uuid.uuid4().hex,
                   walls_version=0, fog_version=0, room_notes_version=0)
        row.pop("created_at", None)
        if map_id is not None:
            row["name"] = name
            row["sort_order"] = conn.execute("SELECT COALESCE(MAX(sort_order),0)+1 FROM maps WHERE campaign_id=?", (target,)).fetchone()[0]
        new = mapping[old] = _insert(conn, "maps", row)
        for table in AUTHORED:
            for item in conn.execute(f"SELECT * FROM {table} WHERE map_id=?", (old,)).fetchall():
                data = dict(item)
                data["map_id"] = new
                identity = data.pop("id", None)
                # Archive source_revision and all historical source_* fields remain intact.
                if "revision" in data:
                    data["revision"] = 1
                if table == "double_reveal_maps":
                    path = (maps_dir / data["image_file"]).resolve()
                    if maps_dir.resolve() not in path.parents:
                        raise ValueError("Invalid alternate image path")
                    stored = images.store_map_image(path.read_bytes(), maps_dir, target)
                    created_files.append(stored.relative_path)
                    if (stored.width, stored.height) != (row["width"], row["height"]):
                        raise ValueError("Alternate image dimensions do not match")
                    data["image_file"] = stored.relative_path
                if table == "double_reveal_rooms":
                    double_links.append((new, data["area_key"], data["destination_map_id"]))
                    data.update(destination_map_id=None, true_active=0)
                if table == "map_transitions":
                    data["id"] = uuid.uuid4().hex
                    destination = data["destination_id"]
                    data.update(destination_id=None, runtime_visibility=None, runtime_availability=None)
                    endpoints.append((identity, data["id"], destination, data["link_defined"]))
                _insert(conn, table, data)
    for mid, key, destination in double_links:
        conn.execute("UPDATE double_reveal_rooms SET destination_map_id=? WHERE map_id=? AND area_key=?",
            (mapping.get(destination), mid, key))
    endpoint_ids = {old: new for old, new, _, _ in endpoints}
    for _, new, destination, defined in endpoints:
        conn.execute("UPDATE map_transitions SET destination_id=?,link_defined=? WHERE id=?",
                     (endpoint_ids.get(destination), int(bool(defined and destination in endpoint_ids)), new))
    if map_id is None:
        for item in conn.execute("SELECT * FROM wall_sources WHERE campaign_id=?", (source_id,)).fetchall():
            row = dict(item)
            row.pop("id")
            row.pop("created_at", None)
            row["campaign_id"] = target
            _insert(conn, "wall_sources", row)
    # Transition triggers bump fog versions; a new copy starts with fresh versions.
    for new in mapping.values():
        conn.execute("UPDATE maps SET walls_version=0,fog_version=0 WHERE id=?", (new,))
    return target, mapping

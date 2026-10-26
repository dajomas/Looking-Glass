"""Campaign-only ZIP backups; archive SQL and filesystem paths are never trusted."""
import base64
import io
import json
import uuid
import zipfile
from . import images
from ..db import MIGRATIONS

MAP_TABLES = ("walls", "fog_ops", "map_fog_snapshots", "map_wall_type_settings", "room_notes", "imported_room_notes", "map_transitions")
WALL_TABLES = ("door_runtime_states", "passage_runtime_states")
TABLES = ("maps", "wall_sources") + MAP_TABLES + WALL_TABLES


def campaign_payload(conn, campaign_id):
    """Serialize campaign rows without writes; caller owns the read transaction."""
    campaign = dict(conn.execute("SELECT * FROM campaigns WHERE id=?", (campaign_id,)).fetchone())
    data = {"format": "looking-glass-campaign", "version": 1, "schema": len(MIGRATIONS),
            "campaign": {k: campaign[k] for k in ("name", "description", "active_map_id")}, "tables": {}}
    for table in TABLES:
        if table in ("maps", "wall_sources"):
            where = "campaign_id=?"
        elif table in WALL_TABLES:
            where = "wall_id IN (SELECT id FROM walls WHERE map_id IN (SELECT id FROM maps WHERE campaign_id=?))"
        else:
            where = "map_id IN (SELECT id FROM maps WHERE campaign_id=?)"
        rows = [dict(r) for r in conn.execute(f"SELECT * FROM {table} WHERE {where} ORDER BY rowid", (campaign_id,))]
        for row in rows:
            if table == "wall_sources":
                row["raw"] = base64.b64encode(row["raw"]).decode("ascii")
            if "created_by" in row:
                row["created_by"] = None
        data["tables"][table] = rows
    return data


def export_campaign(conn, campaign_id, maps_dir):
    conn.execute("BEGIN")
    data = campaign_payload(conn, campaign_id)
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        for row in data["tables"]["maps"]:
            path = (maps_dir / row["image_file"]).resolve()
            if maps_dir.resolve() not in path.parents:
                raise ValueError("Invalid stored image path")
            archive.write(path, f'images/{row["id"]}.png')
        archive.writestr("campaign.json", json.dumps(data, allow_nan=False))
    return out.getvalue()


def restore_campaign(conn, campaign_id, maps_dir, raw, limit, created_files):
    """Caller owns the transaction and removes created_files after rollback."""
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        entries = archive.infolist()
        if len(entries) > 10001 or len({e.filename for e in entries}) != len(entries):
            raise ValueError("Invalid archive entries")
        if sum(e.file_size for e in entries) > limit:
            raise ValueError("Expanded backup exceeds the upload limit")
        data = json.loads(archive.read("campaign.json"))
        if data["format"] != "looking-glass-campaign" or data["version"] != 1 or data["schema"] != len(MIGRATIONS):
            raise ValueError("Unsupported backup format or database schema")
        tables = data["tables"]
        if set(tables) != set(TABLES):
            raise ValueError("Incomplete backup")
        for table, rows in tables.items():
            if not isinstance(rows, list) or len(rows) > 1000000:
                raise ValueError("Invalid backup rows")
            columns = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
            for row in rows:
                if not isinstance(row, dict) or set(row) != columns:
                    raise ValueError("Backup columns do not match this version")
        map_ids = {r["id"] for r in tables["maps"]}
        wall_ids = {r["id"] for r in tables["walls"]}
        transition_ids = {r["id"] for r in tables["map_transitions"]}
        for table, rows in tables.items():
            for row in rows:
                if table in MAP_TABLES and row["map_id"] not in map_ids:
                    raise ValueError("Invalid map reference")
                if table in WALL_TABLES and row["wall_id"] not in wall_ids:
                    raise ValueError("Invalid wall reference")
        active = data["campaign"]["active_map_id"]
        if active is not None and active not in map_ids:
            raise ValueError("Invalid active map")
        conn.execute("UPDATE campaigns SET active_map_id=NULL WHERE id=?", (campaign_id,))
        conn.execute("DELETE FROM map_transition_travel WHERE campaign_id=?", (campaign_id,))
        conn.execute("DELETE FROM maps WHERE campaign_id=?", (campaign_id,))
        conn.execute("DELETE FROM wall_sources WHERE campaign_id=?", (campaign_id,))
        mapping = {}; wall_mapping = {}; transition_mapping = {tid: uuid.uuid4().hex for tid in transition_ids}
        links = []
        for table in TABLES:
            seen = set()
            for original in tables[table]:
                row = dict(original)
                old_id = row.get("id")
                if old_id is not None:
                    if old_id in seen:
                        raise ValueError("Duplicate identity")
                    seen.add(old_id)
                    del row["id"]
                if "campaign_id" in row:
                    row["campaign_id"] = campaign_id
                if "map_id" in row:
                    row["map_id"] = mapping[row["map_id"]]
                if "wall_id" in row:
                    row["wall_id"] = wall_mapping[row["wall_id"]]
                if table == "maps":
                    stored = images.store_map_image(archive.read(f"images/{old_id}.png"), maps_dir, campaign_id)
                    created_files.append(stored.relative_path)
                    if (stored.width, stored.height) != (row["width"], row["height"]):
                        raise ValueError("Map image dimensions do not match")
                    row["image_file"] = stored.relative_path
                    row["cache_token"] = uuid.uuid4().hex
                if table == "wall_sources":
                    row["raw"] = base64.b64decode(row["raw"], validate=True)
                if "created_by" in row:
                    row["created_by"] = None
                if table == "map_transitions":
                    row["id"] = transition_mapping[old_id]
                    destination = row["destination_id"]
                    if destination is not None and destination not in transition_ids:
                        raise ValueError("Invalid transition destination")
                    links.append((row["id"], destination))
                    row["destination_id"] = None
                keys = list(row)
                result = conn.execute(f'INSERT INTO {table} ({",".join(keys)}) VALUES ({",".join("?" for _ in keys)})', [row[k] for k in keys])
                if table == "maps":
                    mapping[old_id] = result.lastrowid
                elif table == "walls":
                    wall_mapping[old_id] = result.lastrowid
        for tid, destination in links:
            conn.execute("UPDATE map_transitions SET destination_id=? WHERE id=?", (transition_mapping.get(destination), tid))
        campaign = data["campaign"]
        if not isinstance(campaign["name"], str) or not 1 <= len(campaign["name"]) <= 120 or not isinstance(campaign["description"], str) or len(campaign["description"]) > 2000:
            raise ValueError("Invalid campaign details")
        conn.execute("UPDATE campaigns SET name=?,description=?,active_map_id=? WHERE id=?", (campaign["name"], campaign["description"], mapping.get(active), campaign_id))

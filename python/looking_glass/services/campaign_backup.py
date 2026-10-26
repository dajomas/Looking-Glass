"""Campaign-only ZIP backups; archive SQL and filesystem paths are never trusted."""
import hashlib
import hmac
import secrets
import time
import os
import sqlite3
import tempfile
from pathlib import Path

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
    if not conn.in_transaction:
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
        if len(raw) > limit:
            raise ValueError("Compressed backup exceeds the upload limit")
        data = json.loads(archive.read("campaign.json"))
        # Migration 16 adds only local checkpoint storage/campaign session_version;
        # the allowlisted portable campaign payload remains identical to schema 15.
        compatible_schema = data["schema"] == len(MIGRATIONS) or (len(MIGRATIONS) == 16 and data["schema"] == 15)
        if data["format"] != "looking-glass-campaign" or data["version"] != 1 or not compatible_schema:
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
        for table, rows in tables.items():
            ids = [r["id"] for r in rows if "id" in r]
            if len(ids) != len(set(ids)):
                raise ValueError("Duplicate identity")
        map_ids = {r["id"] for r in tables["maps"]}
        expected = {"campaign.json"} | {f"images/{mid}.png" for mid in map_ids}
        if {e.filename for e in entries} != expected:
            raise ValueError("Missing or unexpected archive entries")
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


# A restart deliberately invalidates outstanding previews.
_PREVIEW_KEY = secrets.token_bytes(32)
PREVIEW_TTL = 900


def target_digest(conn, campaign_id):
    payload = campaign_payload(conn, campaign_id)
    payload["target"] = dict(conn.execute("SELECT * FROM campaigns WHERE id=?", (campaign_id,)).fetchone())
    return hashlib.sha256(json.dumps(payload, sort_keys=True, allow_nan=False).encode()).hexdigest()


def preview_token(conn, campaign_id, user_id, raw):
    body = json.dumps([campaign_id, user_id, hashlib.sha256(raw).hexdigest(),
                       target_digest(conn, campaign_id), int(time.time())], separators=(",", ":"))
    return body + "." + hmac.new(_PREVIEW_KEY, body.encode(), hashlib.sha256).hexdigest()


def verify_preview(conn, campaign_id, user_id, raw, token):
    try:
        body, signature = token.rsplit(".", 1)
        expected = hmac.new(_PREVIEW_KEY, body.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise ValueError("Invalid preview")
        cid, uid, digest, target, issued = json.loads(body)
        if (cid != campaign_id or uid != user_id or digest != hashlib.sha256(raw).hexdigest()
                or target != target_digest(conn, campaign_id) or not 0 <= time.time() - issued <= PREVIEW_TTL):
            raise ValueError("Preview expired or campaign/archive changed; inspect again")
    except (TypeError, KeyError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid preview") from exc


def inspect_campaign(conn, campaign_id, raw, limit):
    """Trial-import into a private snapshot; never change application rows/files."""
    with tempfile.TemporaryDirectory(prefix="lg-backup-inspect-") as work:
        # File-backed snapshot preserves serialized WAL-mode databases correctly.
        snapshot = Path(work) / "inspection.sqlite3"
        snapshot.write_bytes(conn.serialize())
        clone = sqlite3.connect(snapshot)
        try:
            clone.row_factory = sqlite3.Row
            clone.execute("PRAGMA foreign_keys=ON")
            clone.execute("BEGIN IMMEDIATE")
            restore_campaign(clone, campaign_id, Path(work) / "maps", raw, limit, [])
            if clone.execute("PRAGMA foreign_key_check").fetchone():
                raise ValueError("Invalid backup references")
        finally:
            clone.close()
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        data = json.loads(archive.read("campaign.json"))
        return {"name": data["campaign"]["name"], "description": data["campaign"]["description"],
                "schema": data["schema"], "current_schema": len(MIGRATIONS),
                "maps": [{"name": m["name"], "width": m["width"], "height": m["height"]}
                         for m in data["tables"]["maps"]],
                "counts": {table: len(rows) for table, rows in data["tables"].items()},
                "compressed_bytes": len(raw), "expanded_bytes": sum(e.file_size for e in archive.infolist())}


def save_recovery(conn, campaign_id, maps_dir, recovery_dir, limit):
    """Save and validate a durable portable ZIP before allowing replacement."""
    raw = export_campaign(conn, campaign_id, maps_dir)
    inspect_campaign(conn, campaign_id, raw, limit)
    recovery_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    name = f"campaign-{campaign_id}-{uuid.uuid4().hex}.zip"
    path = recovery_dir / name
    try:
        with path.open("xb") as stream:
            os.chmod(path, 0o600)
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        if os.name != "nt":
            directory = os.open(recovery_dir, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    return name

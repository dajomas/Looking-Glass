"""Read-only, campaign-scoped preparation checks. No repairs or viewer notifications."""
import json
import math
import warnings
from datetime import datetime, timezone
from urllib.parse import urlencode

from PIL import Image
from ..repositories import maps as maps_repo, walls as walls_repo
from .campaign_backup import campaign_payload
from .fog import MapSpec
from .room_notes import area_key
from .wall_type_settings import boundary_segments, disabled_for_map


def inside(x, y, width, height):
    return all(isinstance(v, (int, float)) and math.isfinite(v) for v in (x, y)) and 0 <= x < width and 0 <= y < height


def image_path(maps_dir, relative):
    path = (maps_dir / relative).resolve()
    if maps_dir.resolve() not in path.parents:
        raise ValueError("Image path outside map storage")
    return path


def inspect_url(campaign_id, map_id, x=None, y=None):
    url = f"/campaigns/{campaign_id}/readiness/maps/{map_id}"
    if x is not None and y is not None and all(isinstance(v, (int, float)) and math.isfinite(v) for v in (x,y)):
        url += "?" + urlencode({"x": x, "y": y})
    return url


def check_campaign(conn, campaign, maps_dir, fog, upload_limit):
    """Run within the caller's query-only snapshot; filesystem checks are best-effort."""
    cid = campaign["id"]
    maps = maps_repo.list_for_campaign(conn, cid)
    by_id = {m["id"]: m for m in maps}
    findings = []
    def add(severity, code, message, m=None, x=None, y=None):
        findings.append({"severity": severity, "code": code, "message": message,
                         "map_id": m["id"] if m else None, "map_name": m["name"] if m else "Campaign",
                         "url": inspect_url(cid, m["id"], x, y) if m else f"/campaigns/{cid}#campaign-backup"})
    if not maps:
        add("info", "no_maps", "No maps have been added yet.")
    if campaign["active_map_id"] is not None and campaign["active_map_id"] not in by_id:
        add("error", "active_map", "The active map does not belong to this campaign.")
    image_bytes = 0
    size_complete = True
    for m in maps:
        try:
            path = image_path(maps_dir, m["image_file"])
            image_bytes += path.stat().st_size
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(path) as image:
                    dimensions = image.size
                    image.verify()
                # Force decoding: verify alone is insufficient for some image formats.
                with Image.open(path) as image:
                    image.load()
            if dimensions != (m["width"], m["height"]):
                add("error", "image_dimensions", "Image dimensions differ from stored map dimensions.", m)
        except (OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning):
            size_complete = False
            add("error", "image_unreadable", "Map image is missing, unreadable, unsafe or outside map storage. Check storage or replace the image.", m)
        if not m["wall_count"]:
            add("info", "no_walls", "No walls are configured. This may be intentional; rooms will not be separated by walls.", m)
        notes = conn.execute("SELECT * FROM room_notes WHERE map_id=? ORDER BY area_key", (m["id"],)).fetchall()
        endpoints = conn.execute("SELECT * FROM map_transitions WHERE map_id=? ORDER BY name,id", (m["id"],)).fetchall()
        area = None
        if notes or endpoints:
            try:
                if m["width"] <= 0 or m["height"] <= 0:
                    raise ValueError("Invalid dimensions")
                spec = MapSpec.from_row(m, maps_dir)
                segments = boundary_segments(walls_repo.list_for_map(conn, m["id"]), disabled_for_map(conn, m))
                # No cache files, reconciliation or fog replay: derive current effective topology only.
                area = fog.build_area_map(spec.width, spec.height, segments, spec.calibration, spec.doors_block)
            except (ValueError, TypeError, KeyError, OverflowError):
                add("warning", "geometry_unchecked", "Area geometry could not be checked. Review wall data and calibration; note and arrival checks are incomplete.", m)
        def label(x, y):
            if area is None or not inside(x,y,m["width"],m["height"]):
                return 0
            px, py = int(x*area.scale), int(y*area.scale)
            return int(area.labels[py,px]) if 0 <= py < area.shape[0] and 0 <= px < area.shape[1] else 0
        for note in notes:
            if not inside(note["x"],note["y"],m["width"],m["height"]):
                add("warning", "note_anchor", f'Room note "{note["name"] or "Unnamed"}" is anchored outside the map.', m, note["x"], note["y"])
            elif area is not None:
                lab = label(note["x"],note["y"])
                if not lab or area_key(area,lab,m["width"],m["height"]) != note["area_key"]:
                    add("warning", "stale_note", f'Room note "{note["name"] or "Unnamed"}" no longer matches its area. Review the association; nothing has been removed.', m, note["x"],note["y"])
        for endpoint in endpoints:
            x,y = endpoint["x"],endpoint["y"]
            title = endpoint["name"]
            if not inside(x,y,m["width"],m["height"]):
                add("error", "endpoint_bounds", f'Passage "{title}" is outside the map. Reposition its endpoint.', m,x,y)
            elif area is not None and not label(x,y):
                add("warning", "endpoint_wall", f'Passage "{title}" lies on a wall pixel. Review its arrival position.', m,x,y)
            destination = endpoint["destination_id"]
            if destination:
                # Only query within this campaign; never expose another campaign's data.
                target = conn.execute("SELECT t.map_id FROM map_transitions t JOIN maps m ON m.id=t.map_id WHERE t.id=? AND m.campaign_id=?", (destination,cid)).fetchone()
                if target is None:
                    add("error", "destination_missing", f'Passage "{title}" has a missing or out-of-campaign destination.', m,x,y)
                elif target["map_id"] == m["id"]:
                    add("warning", "destination_same_map", f'Passage "{title}" points to this same map; cross-map travel expects a different map.', m,x,y)
            elif endpoint["link_defined"]:
                add("error", "destination_missing", f'Passage "{title}" has lost its configured destination.', m,x,y)
            else:
                add("info", "destination_unset", f'Passage "{title}" has no outgoing destination. This can be intentional for an arrival-only endpoint.', m,x,y)
    expanded = None
    try:
        payload = campaign_payload(conn,cid)
        expanded = len(json.dumps(payload,allow_nan=False).encode("utf-8")) + image_bytes
        if expanded > upload_limit:
            add("warning", "backup_size", "Current backup content exceeds the expanded restore limit. Increase storage.max_upload_mb or reduce content before relying on a restore.")
        if len(maps) + 1 > 10001:
            add("warning", "backup_entries", "Map count exceeds the current restore archive-entry limit.")
    except (ValueError, TypeError):
        size_complete = False
        add("warning", "backup_unchecked", "Backup size could not be calculated because campaign content cannot be serialized.")
    counts = {s: sum(f["severity"] == s for f in findings) for s in ("error","warning","info")}
    findings.sort(key=lambda f: ({"error":0,"warning":1,"info":2}[f["severity"]], f["map_id"] or 0, f["code"]))
    return {"campaign_id":cid, "generated_at":datetime.now(timezone.utc).isoformat(), "map_count":len(maps),
            "findings":findings, "counts":counts, "expanded_bytes":expanded, "size_complete":size_complete,
            "upload_limit":upload_limit}

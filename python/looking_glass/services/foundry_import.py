"""Import wall data from Foundry VTT (and Universal VTT) exports.

Supported inputs (auto-detected):

* Foundry scene export JSON      - right-click scene > "Export Data" (v9 - v13+)
  { "name": ..., "width": ..., "height": ..., "padding": 0.25, "grid": 100 | {"size": 100},
    "background": {"offsetX": 0, "offsetY": 0}, "walls": [ {"c": [x1,y1,x2,y2], ...}, ... ] }
* A JSON list of wall documents   - [ {"c": [...]}, ... ]  or {"walls": [...]} without scene data
* Foundry NeDB database files     - pre-v11 worlds: data/scenes.db (one scene per line, walls embedded)
                                    or a walls.db / *.db with one wall document per line
* Universal VTT (.dd2vtt/.uvtt/.df2vtt) - Dungeondraft, DungeonFog, Arkenforge etc.
  ("line_of_sight" polylines + "portals" doors, in grid units)

Foundry v11+ stores worlds in LevelDB directories; export the scene with
"Export Data" (or `fvtt package unpack`) and import the resulting JSON.
"""

import json
import math
from collections.abc import Iterable
from typing import Any

from .wall_model import WallSegment, WallSet


class WallImportError(ValueError):
    pass


# ---------------------------------------------------------------------------
# Foundry wall classification
# ---------------------------------------------------------------------------
def _is_v10_values(doc: dict) -> bool:
    """v10+ uses 0/10/20/30/40 for sense types; v9 uses 0/1/2."""
    vals = [doc.get(k) for k in ("move", "sight", "sense", "light", "sound")]
    return any(isinstance(v, (int, float)) and v >= 10 for v in vals)


def classify_foundry_wall(doc: dict) -> tuple[str, bool]:
    """Return (kind, blocks) for a Foundry wall document.

    blocks = True means the wall is an area boundary for reveal purposes.
    Walls that neither block movement nor sight ("ethereal") are ignored.
    Doors are always stored as blocking; whether they split areas is decided
    per map at fog time (maps.doors_block) so it can be toggled without re-import.
    """
    door = int(doc.get("door", 0) or 0)
    move = doc.get("move", 20 if _is_v10_values(doc) else 1)
    sight = doc.get("sight", doc.get("sense", 20 if _is_v10_values(doc) else 1))
    move = 0 if move is None else move
    sight = 0 if sight is None else sight
    v10 = _is_v10_values(doc)

    if door == 1:
        return "door", True
    if door == 2:
        return "secret", True
    if not move and not sight:
        return "ethereal", False
    if not sight:
        return "invisible", True
    limited = (sight == 10) if v10 else (sight == 2)
    if limited:
        return "window", True
    return "wall", True


def _wall_coords(doc: dict) -> tuple[float, float, float, float] | None:
    c = doc.get("c")
    if not isinstance(c, (list, tuple)) or len(c) < 4:
        return None
    try:
        x1, y1, x2, y2 = (float(v) for v in c[:4])
    except (TypeError, ValueError):
        return None
    if x1 == x2 and y1 == y2:
        return None
    return x1, y1, x2, y2


def _segments_from_wall_docs(docs: Iterable[dict]) -> list[WallSegment]:
    out: list[WallSegment] = []
    for doc in docs:
        if not isinstance(doc, dict):
            continue
        coords = _wall_coords(doc)
        if coords is None:
            continue
        kind, blocks = classify_foundry_wall(doc)
        out.append(WallSegment(*coords, kind=kind, blocks=blocks))
    return out


def _grid_size(scene: dict) -> float:
    g = scene.get("grid", 100)
    if isinstance(g, dict):
        g = g.get("size", 100)
    try:
        return float(g) or 100.0
    except (TypeError, ValueError):
        return 100.0


def foundry_scene_origin(scene: dict) -> tuple[float, float]:
    """Top-left of the background image in Foundry canvas coordinates.

    Foundry pads the scene by `padding` (rounded up to whole grid cells) and the
    background may be shifted with background.offsetX/Y (v10+) or shiftX/Y (v9).
    """
    width = float(scene.get("width") or 0)
    height = float(scene.get("height") or 0)
    padding = float(scene.get("padding", 0.25) or 0)
    grid = _grid_size(scene)
    pad_x = math.ceil(width * padding / grid) * grid if width else 0.0
    pad_y = math.ceil(height * padding / grid) * grid if height else 0.0
    bg = scene.get("background") if isinstance(scene.get("background"), dict) else {}
    off_x = float(bg.get("offsetX", scene.get("shiftX", 0)) or 0)
    off_y = float(bg.get("offsetY", scene.get("shiftY", 0)) or 0)
    return pad_x + off_x, pad_y + off_y


def _wallset_from_scene(scene: dict, fmt: str) -> WallSet:
    segments = _segments_from_wall_docs(scene.get("walls") or [])
    ox, oy = foundry_scene_origin(scene) if scene.get("width") else (0.0, 0.0)
    return WallSet(
        name=str(scene.get("name") or "Unnamed scene"),
        segments=segments,
        source_format=fmt,
        scene_width=float(scene["width"]) if scene.get("width") else None,
        scene_height=float(scene["height"]) if scene.get("height") else None,
        origin_x=ox,
        origin_y=oy,
    )


# ---------------------------------------------------------------------------
# Universal VTT
# ---------------------------------------------------------------------------
def _is_uvtt(data: Any) -> bool:
    return isinstance(data, dict) and "resolution" in data and (
        "line_of_sight" in data or "portals" in data or "objects_line_of_sight" in data)


def _parse_uvtt(data: dict, name: str) -> WallSet:
    res = data.get("resolution") or {}
    ppg = float(res.get("pixels_per_grid") or 70)
    origin = res.get("map_origin") or {"x": 0, "y": 0}
    size = res.get("map_size") or {}
    ox, oy = float(origin.get("x", 0)), float(origin.get("y", 0))

    def px(p: dict) -> tuple[float, float]:
        return (float(p["x"]) - ox) * ppg, (float(p["y"]) - oy) * ppg

    segments: list[WallSegment] = []
    for key in ("line_of_sight", "objects_line_of_sight"):
        for poly in data.get(key) or []:
            pts = [px(p) for p in poly if isinstance(p, dict) and "x" in p and "y" in p]
            for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
                if (x1, y1) != (x2, y2):
                    segments.append(WallSegment(x1, y1, x2, y2, "wall", True))
    for portal in data.get("portals") or []:
        bounds = portal.get("bounds") or []
        if len(bounds) >= 2:
            (x1, y1), (x2, y2) = px(bounds[0]), px(bounds[1])
            segments.append(WallSegment(x1, y1, x2, y2, "door", True))
    w = float(size.get("x", 0)) * ppg or None
    h = float(size.get("y", 0)) * ppg or None
    return WallSet(name=name, segments=segments, source_format="uvtt", scene_width=w, scene_height=h)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def _parse_ndjson(text: str) -> list[dict]:
    docs = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise WallImportError(f"Invalid NeDB line: {exc}") from exc
        if isinstance(obj, dict) and not obj.get("$$deleted"):
            docs.append(obj)
    # NeDB is append-only: later lines with the same _id supersede earlier ones.
    by_id: dict[str, dict] = {}
    anon: list[dict] = []
    for d in docs:
        if "_id" in d:
            by_id[d["_id"]] = d
        else:
            anon.append(d)
    return list(by_id.values()) + anon


def parse_wall_file(raw: bytes, filename: str = "") -> list[WallSet]:
    """Parse an uploaded file into one or more WallSets (one per scene)."""
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise WallImportError("File is not UTF-8 text; LevelDB folders cannot be imported directly - "
                              "use the scene's 'Export Data' JSON instead.") from exc

    base = filename.rsplit("/", 1)[-1].rsplit(".", 1)[0] or "Imported walls"
    data: Any
    try:
        data = json.loads(text)
        fmt = "foundry-json"
    except json.JSONDecodeError:
        data = _parse_ndjson(text)
        fmt = "foundry-nedb"

    if _is_uvtt(data):
        return [_parse_uvtt(data, base)]

    sets: list[WallSet] = []
    if isinstance(data, dict):
        if "scenes" in data and isinstance(data["scenes"], list):          # adventure / compendium export
            sets = [_wallset_from_scene(s, fmt) for s in data["scenes"] if isinstance(s, dict)]
        elif "walls" in data:                                              # single scene export
            sets = [_wallset_from_scene(data, fmt)]
        elif "c" in data:                                                  # single wall
            sets = [WallSet(base, _segments_from_wall_docs([data]), fmt)]
    elif isinstance(data, list):
        scenes = [d for d in data if isinstance(d, dict) and "walls" in d]
        if scenes:                                                         # scenes.db
            sets = [_wallset_from_scene(s, fmt) for s in scenes]
        else:                                                              # walls.db / list of walls
            sets = [WallSet(base, _segments_from_wall_docs(data), fmt)]

    sets = [s for s in sets if s.segments]
    if not sets:
        raise WallImportError("No walls found. Expected a Foundry scene export, a wall list, a NeDB "
                              "scenes.db/walls.db file or a Universal VTT (.dd2vtt/.uvtt) file.")
    return sets

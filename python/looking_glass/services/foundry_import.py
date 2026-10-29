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
from collections.abc import Iterable, Sized
from typing import Any

from .wall_model import WallSegment, WallSet


class WallImportError(ValueError):
    pass


def _input_items(value: Any, field: str) -> Iterable:
    # Keep legacy iterable filtering; reject only shapes that cannot be iterated.
    if not isinstance(value, Iterable):
        raise WallImportError(f"{field} must be an iterable collection.")
    return value


def _number(value: Any, field: str, *, positive: bool = False, nonnegative: bool = False) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise WallImportError(f"{field} must be a finite number.") from exc
    if not math.isfinite(result):
        raise WallImportError(f"{field} must be a finite number.")
    if positive and result <= 0:
        raise WallImportError(f"{field} must be positive.")
    if nonnegative and result < 0:
        raise WallImportError(f"{field} must not be negative.")
    return result


def _optional_size(value: Any, field: str) -> float | None:
    return None if value is None else _number(value, field, positive=True)


def validated_calibration(ws: WallSet, image_w: int, image_h: int, *, calibration=None):
    """Check actual target transforms before inspection or wall replacement."""
    _number(image_w, "Target image width", positive=True)
    _number(image_h, "Target image height", positive=True)
    _optional_size(ws.scene_width, "Scene width")
    _optional_size(ws.scene_height, "Scene height")
    try:
        cal = ws.suggested_calibration(image_w, image_h) if calibration is None else calibration
        for field in ("offset_x", "offset_y", "scale_x", "scale_y"):
            _number(getattr(cal, field), f"Calibration {field}", positive=field.startswith("scale"))
        for seg in ws.segments:
            for x, y in ((seg.x1, seg.y1), (seg.x2, seg.y2)):
                tx, ty = cal.apply(x, y)
                _number(tx, "Calibrated wall X")
                _number(ty, "Calibrated wall Y")
    except (TypeError, ValueError, OverflowError, ZeroDivisionError) as exc:
        if isinstance(exc, WallImportError):
            raise
        raise WallImportError("Wall calibration must produce finite coordinates and positive scales.") from exc
    return cal


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
    door_value = doc.get("door", 0) or 0
    try:
        door = int(door_value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise WallImportError("Foundry door must be convertible to an integer.") from exc
    move = doc.get("move", 20 if _is_v10_values(doc) else 1)
    sight = doc.get("sight", doc.get("sense", 20 if _is_v10_values(doc) else 1))
    move = 0 if move is None else move
    sight = 0 if sight is None else sight
    v10 = _is_v10_values(doc)

    if door == 1:
        return ("locked_door" if doc.get("ds") == 2 else "door"), True
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
        coords = tuple(float(v) for v in c[:4])
    except (TypeError, ValueError):
        return None
    except OverflowError as exc:
        raise WallImportError("Wall coordinates must be finite numbers.") from exc
    for value in coords:
        _number(value, "Wall coordinate")
    x1, y1, x2, y2 = coords
    if x1 == x2 and y1 == y2:
        return None
    return x1, y1, x2, y2


def _segments_from_wall_docs(docs: Iterable[dict]) -> list[WallSegment]:
    out: list[WallSegment] = []
    for doc in _input_items(docs, "Foundry walls"):
        if not isinstance(doc, dict):
            continue
        coords = _wall_coords(doc)
        if coords is None:
            continue
        kind, blocks = classify_foundry_wall(doc)
        out.append(WallSegment(*coords, kind=kind, blocks=blocks))
    return out


def _grid_size(scene: dict) -> float:
    g = scene.get("grid")
    if isinstance(g, dict):
        g = g.get("size")
    return _number(100 if g is None else g, "Foundry grid size", positive=True)


def foundry_scene_origin(scene: dict) -> tuple[float, float]:
    """Top-left of the background image in Foundry canvas coordinates."""
    width = _optional_size(scene.get("width"), "Scene width")
    height = _optional_size(scene.get("height"), "Scene height")
    p = scene.get("padding", 0.25)
    padding = _number(0 if p is None else p, "Scene padding", nonnegative=True)
    grid = _grid_size(scene)

    def padded(size: float | None) -> float:
        if size is None:
            return 0.0
        cells = _number(size * padding / grid, "Scene padded grid count", nonnegative=True)
        try:
            return _number(math.ceil(cells) * grid, "Scene padded origin")
        except OverflowError as exc:
            raise WallImportError("Scene padded origin must be finite.") from exc

    bg = scene.get("background") if isinstance(scene.get("background"), dict) else {}
    x = bg.get("offsetX", scene.get("shiftX", 0))
    y = bg.get("offsetY", scene.get("shiftY", 0))
    off_x = _number(0 if x is None else x, "Background offset X")
    off_y = _number(0 if y is None else y, "Background offset Y")
    return (_number(padded(width) + off_x, "Scene origin X"),
            _number(padded(height) + off_y, "Scene origin Y"))


def _scene_image(scene: dict) -> tuple[str, str, bool]:
    bg = scene.get("background")
    ref = (bg.get("src") if isinstance(bg, dict) else None) or scene.get("img") or ""
    ref = ref if isinstance(ref, str) else ""
    if ref.startswith("data:image/"):
        return ref, "", False
    thumb = scene.get("thumb")
    if isinstance(thumb, str) and thumb.startswith("data:image/"):
        return thumb, ref, True
    return "", ref, False


def _wallset_from_scene(scene: dict, fmt: str) -> WallSet:
    segments = _segments_from_wall_docs(scene.get("walls") or [])
    width = _optional_size(scene.get("width"), "Scene width")
    height = _optional_size(scene.get("height"), "Scene height")
    ox, oy = foundry_scene_origin(scene)
    if width is None:
        ox, oy = 0.0, 0.0
    return WallSet(
        name=str(scene.get("name") or "Unnamed scene"), segments=segments,
        source_format=fmt, scene_width=width, scene_height=height,
        origin_x=ox, origin_y=oy,
        image_data=_scene_image(scene)[0], image_reference=_scene_image(scene)[1],
        image_is_thumbnail=_scene_image(scene)[2],
    )


# ---------------------------------------------------------------------------
# Universal VTT
# ---------------------------------------------------------------------------
def _is_uvtt(data: Any) -> bool:
    return isinstance(data, dict) and "resolution" in data and (
        "line_of_sight" in data or "portals" in data or "objects_line_of_sight" in data)


def _parse_uvtt(data: dict, name: str) -> WallSet:
    res = data.get("resolution") or {}
    if not isinstance(res, dict):
        raise WallImportError("UVTT resolution must be an object.")
    ppg_value = res.get("pixels_per_grid")
    ppg = _number(70 if ppg_value is None else ppg_value, "UVTT pixels_per_grid", positive=True)
    origin = res.get("map_origin") or {"x": 0, "y": 0}
    size = res.get("map_size") or {}
    if not isinstance(origin, dict):
        raise WallImportError("UVTT map_origin must be an object.")
    if not isinstance(size, dict):
        raise WallImportError("UVTT map_size must be an object.")
    ox = _number(origin.get("x", 0), "UVTT origin X")
    oy = _number(origin.get("y", 0), "UVTT origin Y")
    width = _optional_size(size.get("x"), "UVTT map width")
    height = _optional_size(size.get("y"), "UVTT map height")
    w = None if width is None else _number(width * ppg, "UVTT pixel width", positive=True)
    h = None if height is None else _number(height * ppg, "UVTT pixel height", positive=True)

    def px(p: dict) -> tuple[float, float]:
        if not isinstance(p, dict) or "x" not in p or "y" not in p:
            raise WallImportError("UVTT point must be an object containing x and y.")
        x = _number(p["x"], "UVTT point X")
        y = _number(p["y"], "UVTT point Y")
        return (_number((x - ox) * ppg, "UVTT transformed X"),
                _number((y - oy) * ppg, "UVTT transformed Y"))

    from .uvtt_export import extension_segments
    try:
        extended = extension_segments(data, ppg, ox, oy)
    except ValueError as exc:
        raise WallImportError(str(exc)) from exc
    if extended is not None:
        ext_name = data["looking_glass"].get("name")
        return WallSet(name=ext_name if isinstance(ext_name, str) and ext_name else name,
                       segments=extended, source_format="uvtt",
                       scene_width=w, scene_height=h,
                       image_data=data.get("image", "") if isinstance(data.get("image", ""), str) else "")

    segments: list[WallSegment] = []
    for key in ("line_of_sight", "objects_line_of_sight"):
        for poly in _input_items(data.get(key) or [], f"UVTT {key}"):
            pts = [px(p) for p in _input_items(poly, f"UVTT {key} polyline")
                   if isinstance(p, dict) and "x" in p and "y" in p]
            for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
                if (x1, y1) != (x2, y2):
                    segments.append(WallSegment(x1, y1, x2, y2, "wall", True))
    for portal in _input_items(data.get("portals") or [], "UVTT portals"):
        if not isinstance(portal, dict):
            raise WallImportError("UVTT portal must be an object.")
        bounds = portal.get("bounds") or []
        if not isinstance(bounds, Sized):
            raise WallImportError("UVTT portal bounds must be a collection of points.")
        if len(bounds) >= 2:
            if not isinstance(bounds, (list, tuple)):
                raise WallImportError("UVTT portal bounds must be a list of point objects.")
            (x1, y1), (x2, y2) = px(bounds[0]), px(bounds[1])
            segments.append(WallSegment(x1, y1, x2, y2, "door", True))
    return WallSet(name=name, segments=segments, source_format="uvtt", scene_width=w, scene_height=h,
                   image_data=data.get("image", "") if isinstance(data.get("image", ""), str) else "")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def _parse_ndjson(text: str) -> list[dict]:
    # Replay identified records before converting documents to wall sets.
    by_id: dict[str, dict] = {}
    anon: list[dict] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise WallImportError(f"Invalid NeDB line: {exc}") from exc
        if not isinstance(obj, dict):
            continue
        if "_id" in obj:
            identity = obj["_id"]
            if not isinstance(identity, str) or not identity:
                raise WallImportError("Invalid NeDB _id: expected a non-empty string.")
            if obj.get("$$deleted"):
                by_id.pop(identity, None)
            else:
                by_id[identity] = obj
        elif not obj.get("$$deleted"):
            anon.append(obj)
    return list(by_id.values()) + anon


def parse_wall_file(raw: bytes, filename: str = "") -> list[WallSet]:
    """Parse an uploaded file into one or more WallSets (one per scene)."""
    if raw.startswith(b"PK\x03\x04"):
        from .pack_images import parse_zip_pack
        return parse_zip_pack(raw, parse_wall_file)
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

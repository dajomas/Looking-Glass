"""UVTT export with a lossless Looking Glass extension; no web or DB dependencies."""

import hashlib
import json
import math
from collections.abc import Iterable

from .wall_model import WallSegment

KINDS = ("wall", "door", "locked_door", "unlocked_door", "secret", "portal", "window", "invisible", "ethereal")
MAX_SEGMENTS = 100_000
MAX_COORD = 10_000_000


def validate_segments(rows) -> list[WallSegment]:
    if not isinstance(rows, list) or len(rows) > MAX_SEGMENTS:
        raise ValueError(f"Expected at most {MAX_SEGMENTS} wall segments.")
    out = []
    for i, row in enumerate(rows):
        if not isinstance(row, (list, tuple)) or len(row) not in (6, 7):
            raise ValueError(f"Wall {i + 1}: expected x1, y1, x2, y2, type, blocks.")
        coords = row[:4]
        if any(type(v) not in (int, float) or abs(v) > MAX_COORD or not math.isfinite(v) for v in coords):
            raise ValueError(f"Wall {i + 1}: coordinates must be finite and within +/-{MAX_COORD}.")
        if coords[0] == coords[2] and coords[1] == coords[3]:
            raise ValueError(f"Wall {i + 1}: endpoints must differ.")
        kind, blocks = row[4:6]
        if kind not in KINDS or type(blocks) is not bool:
            raise ValueError(f"Wall {i + 1}: invalid type or blocking flag.")
        if kind == "ethereal" and blocks:
            raise ValueError(f"Wall {i + 1}: ethereal walls cannot block.")
        out.append(WallSegment(*map(float, coords), kind, blocks, passage=row[6] if len(row) == 7 else {}))
    from .passages import validate_passages
    return validate_passages(out)


def rows_for(segments: Iterable[WallSegment]) -> list[list]:
    return [[s.x1, s.y1, s.x2, s.y2, s.kind, s.blocks] + ([s.passage] if s.passage else []) for s in segments]


def geometry_digest(data: dict) -> str:
    core = {k: data.get(k) for k in ("resolution", "line_of_sight", "objects_line_of_sight", "portals")}
    return hashlib.sha256(json.dumps(core, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def export_uvtt(segments: Iterable[WallSegment], width: int, height: int, name: str,
                pixels_per_grid: float = 70, image: str = "") -> dict:
    if not math.isfinite(pixels_per_grid) or not 0 < pixels_per_grid <= MAX_COORD:
        raise ValueError("pixels_per_grid must be finite and positive.")
    if width <= 0 or height <= 0:
        raise ValueError("Image dimensions must be positive.")
    segments = validate_segments(rows_for(segments))
    ppg = pixels_per_grid
    data = {
        "format": 0.2,
        "resolution": {"map_origin": {"x": 0, "y": 0},
                       "map_size": {"x": width / ppg, "y": height / ppg}, "pixels_per_grid": ppg},
        "line_of_sight": [], "objects_line_of_sight": [], "portals": [], "lights": [],
        "environment": {"baked_lighting": False, "ambient_light": "ffffffff"},
    }
    for s in segments:
        a, b = {"x": s.x1 / ppg, "y": s.y1 / ppg}, {"x": s.x2 / ppg, "y": s.y2 / ppg}
        if not s.blocks or s.kind == "ethereal":
            continue
        if s.kind in ("door", "locked_door", "unlocked_door"):
            data["portals"].append({"position": {"x": (a["x"] + b["x"]) / 2, "y": (a["y"] + b["y"]) / 2},
                                    "bounds": [a, b], "rotation": math.atan2(s.y2 - s.y1, s.x2 - s.x1),
                                    "closed": True, "freestanding": False})
        elif s.kind == "invisible":
            data["objects_line_of_sight"].append([a, b])
        else:
            # Secret doors must not become visible doors in an unaware importer.
            data["line_of_sight"].append([a, b])
    data["looking_glass"] = {
        "version": 2 if any(s.passage or s.kind == "portal" for s in segments) else 1, "name": name, "geometry_sha256": geometry_digest(data),
        "segments": [[s.x1 / ppg, s.y1 / ppg, s.x2 / ppg, s.y2 / ppg, s.kind, s.blocks] + ([s.passage] if s.passage else []) for s in segments],
    }
    if image:
        data["image"] = image
    return data


def extension_segments(data: dict, pixels_per_grid: float, origin_x: float, origin_y: float):
    """None denotes ordinary UVTT; [] denotes an explicitly empty edited set."""
    ext = data.get("looking_glass")
    if ext is None:
        return None
    if not isinstance(ext, dict) or type(ext.get("version")) is not int or ext.get("version") not in (1, 2):
        raise ValueError("Unsupported Looking Glass UVTT extension version.")
    if ext.get("geometry_sha256") != geometry_digest(data):
        raise ValueError("UVTT geometry changed without updating the Looking Glass extension. "
                         "Remove the looking_glass field to import standard geometry only.")
    if not math.isfinite(pixels_per_grid) or pixels_per_grid <= 0:
        raise ValueError("Invalid UVTT pixels_per_grid.")
    if not math.isfinite(origin_x) or not math.isfinite(origin_y):
        raise ValueError("Invalid UVTT origin.")
    grid = validate_segments(ext.get("segments"))
    return validate_segments([[(s.x1 - origin_x) * pixels_per_grid, (s.y1 - origin_y) * pixels_per_grid,
                               (s.x2 - origin_x) * pixels_per_grid, (s.y2 - origin_y) * pixels_per_grid,
                               s.kind, s.blocks] + ([s.passage] if s.passage else []) for s in grid])


def encode_uvtt(data: dict) -> bytes:
    return (json.dumps(data, ensure_ascii=False, allow_nan=False, separators=(",", ":")) + "\n").encode()

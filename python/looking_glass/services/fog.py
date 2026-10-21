"""Fog of war engine.

How area reveal works
---------------------
1. All blocking wall segments are transformed into image space (calibration)
   and rasterised as thick lines onto a "work" bitmap (max `work_max_dim` px).
2. The open (non-wall) pixels are split into 4-connected components with
   scipy.ndimage.label - every component is one area / room enclosed by walls.
3. A fog operation stores only the clicked point. Replaying the ordered ops
   (reveal / hide / reveal_all / hide_all) yields the set of revealed labels.
4. The revealed mask is dilated by the wall thickness so the walls bounding a
   revealed room are visible too, then composited over the map for viewers.

Labels are cached per (map, walls_version); masks per (map, fog_version).
The engine is storage-agnostic: callers pass in plain data.
"""

import io
import hashlib
import math
import threading
from collections import OrderedDict
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Mapping

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

from .wall_model import Calibration, FogOp, WallSegment

DOOR_KINDS = frozenset({"door", "secret", "locked_door", "unlocked_door", "portal"})


@dataclass(slots=True)
class MapSpec:
    id: int
    width: int
    height: int
    image_path: Path
    calibration: Calibration
    doors_block: bool
    walls_version: int
    fog_version: int
    cache_token: str = ""
    door_arrow_color: str = "#46c0ff"
    door_arrows_enabled: bool = True
    locked_door_arrow_color: str = "#ff9f43"
    viewer_door_arrows_enabled: bool | None = None
    arrow_audience: str = "admin"

    @property
    def viewer_arrows_enabled(self) -> bool:
        # Old manually-created specs keep shared behavior; DB rows have an explicit viewer flag.
        return self.door_arrows_enabled if self.viewer_door_arrows_enabled is None else self.viewer_door_arrows_enabled


    @property
    def identity(self) -> str:
        # Includes the random DB incarnation token: deleted IDs cannot alias new maps.
        data = (self.cache_token, str(self.image_path), self.width, self.height,
                self.calibration, self.doors_block, self.door_arrow_color, self.door_arrows_enabled, self.locked_door_arrow_color, self.viewer_arrows_enabled, "passages-v1", self.arrow_audience)
        return hashlib.sha256(repr(data).encode()).hexdigest()[:32]

    @classmethod
    def from_row(cls, row: Mapping[str, Any], maps_dir: Path) -> "MapSpec":
        return cls(
            id=row["id"], width=row["width"], height=row["height"],
            image_path=maps_dir / row["image_file"],
            calibration=Calibration(row["wall_offset_x"], row["wall_offset_y"],
                                    row["wall_scale_x"], row["wall_scale_y"]),
            doors_block=bool(row["doors_block"]),
            walls_version=row["walls_version"], fog_version=row["fog_version"],
            locked_door_arrow_color=row["locked_door_arrow_color"] if "locked_door_arrow_color" in row.keys() else "#ff9f43",
            door_arrow_color=row["door_arrow_color"] if "door_arrow_color" in row.keys() else "#46c0ff",
            door_arrows_enabled=bool(row["door_arrows_enabled"]) if "door_arrows_enabled" in row.keys() else True,
            viewer_door_arrows_enabled=bool(row["viewer_door_arrows_enabled"]) if "viewer_door_arrows_enabled" in row.keys() else bool(row["door_arrows_enabled"]) if "door_arrows_enabled" in row.keys() else True,
            cache_token=row["cache_token"] if "cache_token" in row.keys() else "",
        )


@dataclass(slots=True)
class AreaMap:
    labels: np.ndarray      # int32 (h, w); 0 = wall pixel
    count: int              # number of areas
    sizes: np.ndarray       # pixel count per label
    scale: float            # work px per image px
    region_slices: list | None = field(default=None, repr=False, compare=False)
    region_signatures: dict = field(default_factory=dict, repr=False, compare=False)

    @property
    def shape(self) -> tuple[int, int]:
        return self.labels.shape  # (h, w)


@dataclass(slots=True)
class RevealResult:
    label: int
    fraction: float         # share of the map covered by the clicked area
    leak_warning: bool


class _LRU[K, V]:
    def __init__(self, size: int):
        self.size = size
        self._d: OrderedDict[K, V] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: K) -> V | None:
        with self._lock:
            if key in self._d:
                self._d.move_to_end(key)
                return self._d[key]
            return None

    def put(self, key: K, value: V) -> None:
        with self._lock:
            self._d[key] = value
            self._d.move_to_end(key)
            while len(self._d) > self.size:
                self._d.popitem(last=False)

    def drop_map(self, map_id: int) -> None:
        with self._lock:
            for k in [k for k in self._d if k[0] == map_id]:
                del self._d[k]


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    c = color.lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


class FogEngine:
    def __init__(self, fog_cfg: Mapping[str, Any], viewer_cfg: Mapping[str, Any], cache_dir: Path):
        self.work_max_dim = int(fog_cfg["work_max_dim"])
        self.thickness = max(1, int(fog_cfg["wall_thickness"]))
        self.leak_fraction = float(fog_cfg["leak_warn_fraction"])
        self.feather = float(fog_cfg["feather_px"])
        self.fog_rgb = _hex_to_rgb(str(fog_cfg["fog_color"]))
        self.viewer_max_dim = int(viewer_cfg["max_image_dim"])
        self.viewer_format = str(viewer_cfg["image_format"]).lower()
        self.viewer_quality = int(viewer_cfg["image_quality"])
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._areas: _LRU[tuple, AreaMap] = _LRU(8)
        self._masks: _LRU[tuple, np.ndarray] = _LRU(16)
        self._map_locks: dict[int, threading.RLock] = {}
        self._locks_guard = threading.Lock()

    # ------------------------------------------------------------------ utils
    def _lock(self, map_id: int) -> threading.RLock:
        with self._locks_guard:
            return self._map_locks.setdefault(map_id, threading.RLock())

    def work_scale(self, width: int, height: int) -> float:
        return min(1.0, self.work_max_dim / max(width, height, 1))

    def invalidate(self, map_id: int) -> None:
        with self._lock(map_id):
            self._areas.drop_map(map_id)
            self._masks.drop_map(map_id)
            for f in self.cache_dir.glob(f"viewer_{map_id}_*"):
                f.unlink(missing_ok=True)
            for f in self.cache_dir.glob(f"base_{map_id}_*"):
                f.unlink(missing_ok=True)

    def cache_identity(self, spec: MapSpec) -> str:
        config = ("fog-cache-v2", spec.identity, self.work_max_dim, self.thickness,
                  self.feather, self.fog_rgb, self.viewer_max_dim,
                  self.viewer_format, self.viewer_quality)
        return hashlib.sha256(repr(config).encode()).hexdigest()[:32]

    @staticmethod
    def active_segments(segments: list[WallSegment], doors_block: bool) -> list[WallSegment]:
        return [s for s in segments if s.blocks and (doors_block or s.kind not in DOOR_KINDS)]

    # ------------------------------------------------------------- area map
    def area_map(self, spec: MapSpec, segments: list[WallSegment]) -> AreaMap:
        key = (spec.id, self.cache_identity(spec), spec.walls_version)
        cached = self._areas.get(key)
        if cached is not None:
            return cached
        with self._lock(spec.id):
            cached = self._areas.get(key)
            if cached is None:
                cached = self.build_area_map(spec.width, spec.height, segments, spec.calibration, spec.doors_block)
                self._areas.put(key, cached)
        return cached

    def build_area_map(self, width: int, height: int, segments: list[WallSegment],
                       calibration: Calibration, doors_block: bool) -> AreaMap:
        scale = self.work_scale(width, height)
        ww, wh = max(1, math.ceil(width * scale)), max(1, math.ceil(height * scale))
        wall_img = Image.new("L", (ww, wh), 0)
        draw = ImageDraw.Draw(wall_img)
        r = self.thickness / 2
        for s in self.active_segments(segments, doors_block):
            x1, y1 = calibration.apply(s.x1, s.y1)
            x2, y2 = calibration.apply(s.x2, s.y2)
            p1, p2 = (x1 * scale, y1 * scale), (x2 * scale, y2 * scale)
            draw.line([p1, p2], fill=255, width=self.thickness)
            for px, py in (p1, p2):  # round caps close gaps at corners
                draw.ellipse([px - r, py - r, px + r, py + r], fill=255)
        open_px = np.asarray(wall_img) == 0
        labels, count = ndimage.label(open_px)  # default structure = 4-connectivity
        sizes = np.bincount(labels.ravel(), minlength=count + 1)
        return AreaMap(labels=labels.astype(np.int32), count=int(count), sizes=sizes, scale=scale)

    def label_at(self, area: AreaMap, x: float, y: float) -> int:
        h, w = area.shape
        px = min(max(int(x * area.scale), 0), w - 1)
        py = min(max(int(y * area.scale), 0), h - 1)
        lab = int(area.labels[py, px])
        if lab:
            return lab
        # Clicked on a wall line: pick the nearest open pixel within a small radius.
        radius = self.thickness * 3
        y0, y1 = max(0, py - radius), min(h, py + radius + 1)
        x0, x1 = max(0, px - radius), min(w, px + radius + 1)
        window = area.labels[y0:y1, x0:x1]
        ys, xs = np.nonzero(window)
        if len(ys) == 0:
            return 0
        d = (ys + y0 - py) ** 2 + (xs + x0 - px) ** 2
        i = int(np.argmin(d))
        return int(window[ys[i], xs[i]])

    def describe_click(self, area: AreaMap, x: float, y: float) -> RevealResult:
        lab = self.label_at(area, x, y)
        total = area.labels.size
        frac = float(area.sizes[lab]) / total if lab else 0.0
        return RevealResult(label=lab, fraction=frac, leak_warning=frac >= self.leak_fraction)

    # ------------------------------------------------------------------ masks
    def revealed_labels(self, area: AreaMap, ops: list[FogOp]) -> set[int]:
        revealed: set[int] = set()
        for op in ops:
            match op.op:
                case "reveal_all":
                    revealed = set(range(1, area.count + 1))
                case "hide_all":
                    revealed = set()
                case "reveal" | "hide" if op.x is not None and op.y is not None:
                    lab = self.label_at(area, op.x, op.y)
                    if lab:
                        (revealed.add if op.op == "reveal" else revealed.discard)(lab)
        return revealed

    def mask(self, spec: MapSpec, segments: list[WallSegment], ops: list[FogOp]) -> np.ndarray:
        """Boolean revealed-mask at work resolution."""
        key = (spec.id, self.cache_identity(spec), spec.walls_version, spec.fog_version)
        cached = self._masks.get(key)
        if cached is not None:
            return cached
        area = self.area_map(spec, segments)
        revealed = self.revealed_labels(area, ops)
        if area.count and len(revealed) == area.count:
            m = np.ones(area.shape, dtype=bool)
        elif not revealed:
            m = np.zeros(area.shape, dtype=bool)
        else:
            m = np.isin(area.labels, np.fromiter(revealed, dtype=np.int32))
            m = ndimage.binary_dilation(m, iterations=self.thickness)
        self._masks.put(key, m)
        return m

    def admin_mask_png(self, spec: MapSpec, segments: list[WallSegment], ops: list[FogOp]) -> bytes:
        """RGBA PNG at work resolution; alpha 255 where revealed."""
        m = self.mask(spec, segments, ops)
        alpha = Image.fromarray((m * 255).astype(np.uint8), "L")
        img = Image.new("RGBA", alpha.size, (255, 255, 255, 0))
        img.putalpha(alpha)
        buf = io.BytesIO()
        img.save(buf, "PNG", optimize=False, compress_level=3)
        return buf.getvalue()

    # -------------------------------------------------------- viewer image
    def _base_image(self, spec: MapSpec) -> Image.Image:
        path = self.cache_dir / f"base_{spec.id}_{self.cache_identity(spec)}_{spec.walls_version}.png"
        if path.exists():
            return Image.open(path).convert("RGB")
        with Image.open(spec.image_path) as src:
            img = src.convert("RGB")
        img.thumbnail((self.viewer_max_dim, self.viewer_max_dim), Image.Resampling.LANCZOS)
        for f in self.cache_dir.glob(f"base_{spec.id}_*.png"):
            f.unlink(missing_ok=True)
        img.save(path, "PNG", compress_level=1)
        return img

    @property
    def viewer_ext(self) -> str:
        return {"jpeg": "jpg", "jpg": "jpg", "png": "png"}.get(self.viewer_format, "webp")

    @property
    def viewer_media_type(self) -> str:
        return {"jpg": "image/jpeg", "png": "image/png"}.get(self.viewer_ext, "image/webp")

    def door_arrow_overlay(self, spec, segments, ops):
        from .door_arrows import overlay
        return overlay(self, spec, segments, ops)

    def door_arrows_png(self, spec, segments, ops) -> bytes:
        buf = io.BytesIO()
        self.door_arrow_overlay(spec, segments, ops).save(buf, "PNG")
        return buf.getvalue()

    def viewer_image(self, spec: MapSpec, segments: list[WallSegment], ops: list[FogOp]) -> Path:
        """Composite the fogged map with viewer-only arrow visibility; never mutate admin state."""
        spec = replace(spec, door_arrows_enabled=spec.viewer_arrows_enabled, arrow_audience="viewer")
        out = self.cache_dir / f"viewer_{spec.id}_{self.cache_identity(spec)}_{spec.walls_version}_{spec.fog_version}.{self.viewer_ext}"
        if out.exists():
            return out
        with self._lock(spec.id):
            if out.exists():
                return out
            m = self.mask(spec, segments, ops)
            base = self._base_image(spec)
            fog = Image.new("RGB", base.size, self.fog_rgb)
            if not m.any():
                composed = fog
            else:
                mask_img = Image.fromarray((m * 255).astype(np.uint8), "L").resize(base.size, Image.Resampling.BILINEAR)
                if self.feather > 0:
                    mask_img = mask_img.filter(ImageFilter.GaussianBlur(self.feather))
                composed = Image.composite(base, fog, mask_img)
            arrows = self.door_arrow_overlay(spec, segments, ops).resize(base.size, Image.Resampling.NEAREST)
            composed.paste(arrows, (0, 0), arrows)
            for f in self.cache_dir.glob(f"viewer_{spec.id}_*"):
                f.unlink(missing_ok=True)
            tmp = out.with_suffix(".tmp")
            params: dict[str, Any] = {}
            if self.viewer_ext == "webp":
                params = {"quality": self.viewer_quality, "method": 2}   # method 2: much faster, near-equal size
            elif self.viewer_ext == "jpg":
                params = {"quality": self.viewer_quality, "optimize": True}
            composed.save(tmp, {"jpg": "JPEG", "png": "PNG"}.get(self.viewer_ext, "WEBP"), **params)
            tmp.replace(out)
        return out

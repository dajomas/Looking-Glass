"""Plain data structures shared by the importer, repositories and fog engine."""

from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class WallSegment:
    x1: float
    y1: float
    x2: float
    y2: float
    kind: str = "wall"     # wall | door | locked_door | unlocked_door | secret | window | invisible | ethereal
    id: int = field(default=0, compare=False, kw_only=True)
    passage: dict = field(default_factory=dict, compare=False, kw_only=True)
    runtime: dict = field(default_factory=dict, compare=False, kw_only=True)
    designed_kind: str = field(default="", compare=False, kw_only=True)
    blocks: bool = True    # whether it separates areas


@dataclass(slots=True, frozen=True)
class Calibration:
    """Transforms source (scene) coordinates into map image pixels:
    image = (source - offset) * scale
    """
    offset_x: float = 0.0
    offset_y: float = 0.0
    scale_x: float = 1.0
    scale_y: float = 1.0

    def apply(self, x: float, y: float) -> tuple[float, float]:
        return (x - self.offset_x) * self.scale_x, (y - self.offset_y) * self.scale_y


@dataclass(slots=True, frozen=True)
class FogOp:
    op: str                 # reveal | hide | reveal_all | hide_all
    x: float | None = None  # image coordinates
    y: float | None = None


@dataclass(slots=True)
class WallSet:
    """One importable set of walls (usually one Foundry scene)."""
    name: str
    segments: list[WallSegment] = field(default_factory=list)
    source_format: str = ""
    scene_width: float | None = None
    scene_height: float | None = None
    # Suggested calibration, before scaling to the actual image size
    origin_x: float = 0.0
    origin_y: float = 0.0
    image_data: str = ""
    image_reference: str = ""
    image_is_thumbnail: bool = False

    def suggested_calibration(self, image_w: int, image_h: int) -> Calibration:
        sx = image_w / self.scene_width if self.scene_width else 1.0
        sy = image_h / self.scene_height if self.scene_height else 1.0
        return Calibration(self.origin_x, self.origin_y, sx, sy)

"""Shared arrow geometry, raster rendering and server-validated click targets."""
import math
from dataclasses import dataclass
import numpy as np
from PIL import Image, ImageDraw


@dataclass(frozen=True)
class DoorArrow:
    source_label: int
    target: tuple[float, float]
    polygon: list[tuple[float, float]]  # work-pixel coordinates
    wall_id: int = 0
    kind: str = "door"


def arrows(engine, spec, segments, ops):
    if not spec.door_arrows_enabled or not spec.doors_block:
        return []
    area = engine.area_map(spec, segments)
    revealed = engine.revealed_labels(area, ops)
    if not revealed or len(revealed) == area.count:
        return []
    h, w = area.shape
    result = []
    for seg in segments:
        if seg.kind not in ("door", "locked_door", "unlocked_door") or not seg.blocks:
            continue
        x1, y1 = spec.calibration.apply(seg.x1, seg.y1)
        x2, y2 = spec.calibration.apply(seg.x2, seg.y2)
        dx, dy = (x2-x1)*area.scale, (y2-y1)*area.scale
        length = math.hypot(dx, dy)
        if length < 1:
            continue
        nx, ny = -dy/length, dx/length
        mx, my = (x1+x2)*area.scale/2, (y1+y2)*area.scale/2
        sides = []
        for sign in (-1, 1):
            hit = None
            for distance in range(1, engine.thickness*3+4):
                x, y = mx+sign*nx*distance, my+sign*ny*distance
                if not (0 <= x < w and 0 <= y < h):
                    break
                label = int(area.labels[int(y), int(x)])
                if label:
                    # Store the center of a verified open pixel, never guess past a wall.
                    hit = (label, sign, distance, (int(x)+.5)/area.scale, (int(y)+.5)/area.scale)
                    break
            sides.append(hit)
        if not all(sides):
            continue
        a, b = sides
        if a[0] == b[0] or (a[0] in revealed) == (b[0] in revealed):
            continue
        source, target = (a, b) if a[0] in revealed else (b, a)
        label, sign, distance, _, _ = source
        ux, uy = sign*nx, sign*ny
        size = max(8, min(24, length*.7))
        tip = (mx+ux*(distance+2), my+uy*(distance+2))
        def point(back, across):
            return (tip[0]+ux*back-uy*across, tip[1]+uy*back+ux*across)
        polygon = [point(0,0),point(size*.48,-size*.38),point(size*.48,-size*.14),
                   point(size,-size*.14),point(size,size*.14),point(size*.48,size*.14),point(size*.48,size*.38)]
        result.append(DoorArrow(label, (target[3], target[4]), polygon, seg.id, seg.kind))
    return result


def overlay(engine, spec, segments, ops):
    scale = engine.work_scale(spec.width, spec.height)
    w, h = max(1, math.ceil(spec.width*scale)), max(1, math.ceil(spec.height*scale))
    image = Image.new("RGBA", (w,h))
    items = arrows(engine, spec, segments, ops)
    if not items:
        return image
    draw = ImageDraw.Draw(image)
    for item in items:
        color = (spec.locked_door_arrow_color if item.kind == "locked_door" else spec.door_arrow_color).lstrip("#")
        rgb = tuple(int(color[i:i+2],16) for i in (0,2,4))
        draw.polygon(item.polygon, fill=(*rgb,255))
    area = engine.area_map(spec, segments)
    revealed = engine.revealed_labels(area, ops)
    pixels = np.array(image)
    pixels[~np.isin(area.labels,list(revealed)),3] = 0
    return Image.fromarray(pixels)


def hit_at(engine, spec, segments, ops, x, y):
    """Return only the hidden adjacent room target for an actual visible arrow pixel."""
    if not (math.isfinite(x) and math.isfinite(y) and 0 <= x < spec.width and 0 <= y < spec.height):
        return None
    items = arrows(engine, spec, segments, ops)
    if not items:
        return None
    area = engine.area_map(spec, segments)
    px, py = int(x*area.scale), int(y*area.scale)
    revealed = engine.revealed_labels(area, ops)
    if int(area.labels[py,px]) not in revealed:
        return None
    # Use the identical rasterizer and coordinates as the displayed overlay.
    for item in reversed(items):
        image = Image.new("L", (area.shape[1],area.shape[0]))
        ImageDraw.Draw(image).polygon(item.polygon,fill=255)
        if image.getpixel((px,py)):
            return item
    return None


def target_at(engine, spec, segments, ops, x, y):
    """Legacy reveal endpoint must never bypass a locked arrow."""
    item = hit_at(engine, spec, segments, ops, x, y)
    return item.target if item and item.kind != "locked_door" else None

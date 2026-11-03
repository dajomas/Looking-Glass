"""Passage arrows shared by server compositing and validated admin hit testing."""
import math
from dataclasses import dataclass, replace
import numpy as np
from PIL import Image, ImageDraw
from .passages import entry_kind


@dataclass(frozen=True)
class DoorArrow:
    source_label: int
    target: tuple[float, float]
    polygon: list[tuple[float, float]]
    wall_id: int = 0
    kind: str = "door"
    side: int = -1
    portal: bool = False
    exit_only: bool = False
    secret_origin: bool = False


def _geometry(engine, spec, area, seg):
    x1,y1 = spec.calibration.apply(seg.x1,seg.y1)
    x2,y2 = spec.calibration.apply(seg.x2,seg.y2)
    dx,dy = (x2-x1)*area.scale,(y2-y1)*area.scale
    length = math.hypot(dx,dy)
    if length < 1:
        return None
    nx,ny = -dy/length,dx/length
    mx,my = (x1+x2)*area.scale/2,(y1+y2)*area.scale/2
    sides = []
    h,w = area.shape
    for sign in (-1,1):
        hit = None
        for distance in range(1,engine.thickness*3+4):
            x,y = mx+sign*nx*distance,my+sign*ny*distance
            if not (0<=x<w and 0<=y<h):
                break
            label = int(area.labels[int(y),int(x)])
            if label:
                hit = (label,sign,distance,(int(x)+.5)/area.scale,(int(y)+.5)/area.scale)
                break
        sides.append(hit)
    return (mx,my,nx,ny,max(8,min(24,length*.7)),sides)


def _polygon(geo, source, outward=False, both=False):
    mx,my,nx,ny,size,_ = geo
    _,sign,distance,_,_ = source
    ux,uy = sign*nx,sign*ny
    tip = (mx+ux*(distance+2),my+uy*(distance+2))
    def point(back,across):
        return (tip[0]+ux*back-uy*across,tip[1]+uy*back+ux*across)
    if both:
        points = [(0,0),(.35,-.38),(.35,-.14),(.65,-.14),(.65,-.38),(1,0),(.65,.38),(.65,.14),(.35,.14),(.35,.38)]
    else:
        points = [(0,0),(.48,-.38),(.48,-.14),(1,-.14),(1,.14),(.48,.14),(.48,.38)]
        if outward:
            points = [(1-a,b) for a,b in points]
    return [point(a*size,b*size) for a,b in points]


def arrows(engine,spec,segments,ops):
    viewer = getattr(spec,"arrow_audience","admin") == "viewer"
    exceptions = viewer and (spec.viewer_portal_arrows_enabled or spec.viewer_secret_arrows_enabled)
    if (not spec.door_arrows_enabled and not exceptions) or not spec.doors_block:
        return []
    area = engine.area_map(spec,segments)
    revealed = engine.revealed_labels(area,ops)
    if not revealed:
        return []
    viewer = getattr(spec,"arrow_audience","admin") == "viewer"
    geos = {s.id:_geometry(engine,spec,area,s) for s in segments if s.kind == "portal" and s.blocks}
    pairs = {(s.passage.get("pair"),s.passage.get("end")):s for s in segments if s.kind == "portal"}
    result, exits = [], {}
    for seg in segments:
        if not seg.blocks:
            continue
        if seg.kind == "portal":
            geo = geos.get(seg.id)
            if geo is None:
                continue
            other = pairs.get((seg.passage.get("pair"), "b" if seg.passage.get("end")=="a" else "a"))
            other_geo = geos.get(other.id) if other else None
            if other_geo is None:
                continue
            for i,side in enumerate(seg.passage["sides"]):
                source = geo[-1][i]
                if side["role"] not in ("entry","both") or not source or source[0] not in revealed:
                    continue
                target = other_geo[-1][side["exit"]]
                if not target:
                    continue
                kind = entry_kind(seg,i)
                if viewer and kind == "secret":
                    continue
                result.append(DoorArrow(source[0],(target[3],target[4]),_polygon(geo,source,both=side["role"]=="both"),
                                        seg.id,kind,i,True,False,side.get("kind")=="secret"))
                if not viewer:
                    exits[(other.id,side["exit"])] = (other,other_geo,target)
            continue
        if seg.kind not in ("door","locked_door","unlocked_door","secret"):
            continue
        geo = _geometry(engine,spec,area,seg)
        if not geo or not all(geo[-1]):
            continue
        a,b = geo[-1]
        if a[0]==b[0]:
            continue
        persistent = (seg.designed_kind or seg.kind) == "secret"
        if viewer and seg.kind == "secret":
            continue
        for source,target in ((a,b),(b,a)):
            if source[0] not in revealed or (target[0] in revealed and not persistent):
                continue
            result.append(DoorArrow(source[0],(target[3],target[4]),_polygon(geo,source),seg.id,seg.kind,-1,False,False,persistent))
    if not viewer:
        for (wall_id,i),(seg,geo,target) in exits.items():
            if any(a.wall_id==wall_id and a.side==i and a.portal for a in result):
                continue
            result.insert(0,DoorArrow(target[0],(target[3],target[4]),_polygon(geo,target,outward=True),wall_id,"door",i,True,True))
    if viewer and not spec.door_arrows_enabled:
        result = [item for item in result if viewer_exception_visible(spec, item)]
    return result


def viewer_exception_visible(spec, item):
    """Union of exceptions; currently secret entries never reach the viewer."""
    return item.kind != "secret" and not item.exit_only and (
        (item.portal and spec.viewer_portal_arrows_enabled) or
        (item.secret_origin and spec.viewer_secret_arrows_enabled))


def arrow_color(item,spec):
    if item.portal:
        return "#ff5252" if item.kind=="secret" else "#a66a3f" if item.kind in ("locked_door","unlocked_door") else "#c0c0c0"
    if item.kind=="secret":
        return "#b07cff"
    return spec.locked_door_arrow_color if item.kind=="locked_door" else spec.door_arrow_color


def overlay(engine,spec,segments,ops):
    scale = engine.work_scale(spec.width,spec.height)
    image = Image.new("RGBA",(max(1,math.ceil(spec.width*scale)),max(1,math.ceil(spec.height*scale))))
    area = engine.area_map(spec,segments)
    revealed = engine.revealed_labels(area,ops)
    entry_layer = Image.new("RGBA",image.size)
    exit_draw,entry_draw = ImageDraw.Draw(image),ImageDraw.Draw(entry_layer)
    for item in arrows(engine,spec,segments,ops):
        display_item = item
        if getattr(spec,"arrow_audience","admin") == "viewer" and item.kind in ("locked_door","unlocked_door"):
            display_item = replace(item,kind="door")
        color = arrow_color(display_item,spec).lstrip("#")
        rgb = tuple(int(color[i:i+2],16) for i in (0,2,4))
        (exit_draw if item.exit_only else entry_draw).polygon(item.polygon,fill=(*rgb,255))
    pixels = np.array(entry_layer)
    pixels[~np.isin(area.labels,list(revealed)),3] = 0
    return Image.alpha_composite(image,Image.fromarray(pixels))


def hit_at(engine,spec,segments,ops,x,y):
    if not (math.isfinite(x) and math.isfinite(y) and 0<=x<spec.width and 0<=y<spec.height):
        return None
    area = engine.area_map(spec,segments)
    px,py = int(x*area.scale),int(y*area.scale)
    if int(area.labels[py,px]) not in engine.revealed_labels(area,ops):
        return None
    for item in reversed(arrows(engine,spec,segments,ops)):
        image = Image.new("L",(area.shape[1],area.shape[0]))
        ImageDraw.Draw(image).polygon(item.polygon,fill=255)
        if image.getpixel((px,py)):
            return None if item.exit_only else item
    return None


def target_at(engine,spec,segments,ops,x,y):
    item = hit_at(engine,spec,segments,ops,x,y)
    return item.target if item and item.kind not in ("locked_door","secret") else None

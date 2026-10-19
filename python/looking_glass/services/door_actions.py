"""Storage-aware door actions, independent of HTTP. Caller authorizes and owns transaction."""
import math
from .door_arrows import arrows, hit_at
from .door_runtime import decide, set_kind
from .map_display import checkpoint_if_active
from ..repositories import fog_ops as fog_repo, maps as maps_repo


def distance(x,y,a,b,c,d):
    dx,dy=c-a,d-b
    t=max(0,min(1,((x-a)*dx+(y-b)*dy)/(dx*dx+dy*dy or 1)))
    return math.hypot(x-a-t*dx,y-b-t*dy)


def perform(conn,engine,spec,segs,ops,body,user_id):
    stamp=(spec.cache_token,spec.walls_version,spec.fog_version)
    if stamp!=(body.cache_token,body.walls_version,body.fog_version):
        raise ValueError("The map changed; refresh and try the door again.")
    wall=next((s for s in segs if s.id==body.wall_id),None)
    if wall is None or wall.kind not in ("locked_door","unlocked_door"):
        raise ValueError("No locked/unlocked door on this map.")
    if body.gesture not in ("single","double") or body.hit not in ("arrow","wall") or body.mode not in ("reveal","hide"):
        raise ValueError("Invalid door action.")
    if not (math.isfinite(body.x) and math.isfinite(body.y) and 0<=body.x<spec.width and 0<=body.y<spec.height):
        raise ValueError("Click inside the map.")
    item=None
    if body.hit=="arrow":
        item=hit_at(engine,spec,segs,ops,body.x,body.y)
        if item is None or item.wall_id!=wall.id:
            raise ValueError("No enabled arrow for this door at that point.")
    else:
        a,b=spec.calibration.apply(wall.x1,wall.y1)
        c,d=spec.calibration.apply(wall.x2,wall.y2)
        if not (math.isfinite(body.tolerance) and 0<body.tolerance<=500) or distance(body.x,body.y,a,b,c,d)>body.tolerance:
            raise ValueError("Click on the door segment.")
    action=decide(wall.kind,body.gesture,body.hit)
    if action in ("lock","unlock"):
        set_kind(conn,spec.id,wall.id,"locked_door" if action=="lock" else "unlocked_door")
        return {"door_action":action},True
    if action=="none":
        return {"door_action":"none"},False
    # An unlocked arrow reveals; a wall segment retains the normal selected fog mode.
    target=item.target if item else (body.x,body.y)
    op="reveal" if item else body.mode
    res=engine.describe_click(engine.area_map(spec,segs),*target)
    if not res.label:
        raise ValueError("No open area behind the door.")
    fog_repo.add(conn,spec.id,op,*target,user_id)
    maps_repo.bump_fog(conn,spec.id)
    checkpoint_if_active(conn,spec.id)
    return {"door_action":op,"area_fraction":round(res.fraction,4),"leak_warning":res.leak_warning},True

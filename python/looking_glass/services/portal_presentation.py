"""Admin-only route associations for presentation; never changes fog or viewer data."""
import math


def _compass(spec,segment,side):
    x1,y1=spec.calibration.apply(segment.x1,segment.y1)
    x2,y2=spec.calibration.apply(segment.x2,segment.y2)
    angle=(math.degrees(math.atan2(y2-y1,x2-x1))+360)%360
    heading=(math.floor((angle+22.5+1e-10)/45)+(4 if side==1 else 0))%8
    return ("N","NE","E","SE","S","SW","W","NW")[heading]


def visible_routes(spec,segments,arrow_objects):
    """Associate actual displayed Entry/Exit arrows, including shared and Both exits.

    Input arrow_objects must be the admin geometry for the current boundary/fog
    state. Only actual existing polygons are returned, never guessed destinations.
    """
    if getattr(spec,"arrow_audience","admin")!="admin" or not spec.door_arrows_enabled:
        return []
    by_id={s.id:s for s in segments}
    sections={s.id:i+1 for i,s in enumerate(segments)}
    paired={(s.passage.get("pair"),s.passage.get("end")):s for s in segments if s.kind=="portal"}
    geometry={(a.wall_id,a.side):a for a in arrow_objects if a.portal}
    result=[]
    def endpoint(segment,side,arrow):
        return {"wall_id":segment.id,"section":sections[segment.id],"side":side,
                "compass":_compass(spec,segment,side),"polygon":arrow.polygon}
    for arrow in arrow_objects:
        if not arrow.portal or arrow.exit_only:
            continue
        segment=by_id.get(arrow.wall_id)
        if segment is None or segment.kind!="portal":
            continue
        side=segment.passage["sides"][arrow.side]
        other=paired.get((segment.passage["pair"],"b" if segment.passage["end"]=="a" else "a"))
        target_side=side.get("exit")
        if other is None or type(target_side) is not int or target_side not in (0,1):
            continue
        target=geometry.get((other.id,target_side))
        if target is None:
            continue
        result.append({"id":f"{segment.id}:{arrow.side}>{other.id}:{target_side}",
                       "entry":endpoint(segment,arrow.side,arrow),"exit":endpoint(other,target_side,target),
                       "state":arrow.kind})
    return result

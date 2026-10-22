"""Cross-map endpoints and atomic travel; callers own authorization and transactions."""
import json
import math
import uuid
from ..repositories import maps, campaigns, fog_ops
from .map_display import checkpoint

KINDS={"stairs","ladder","hole","portal","climb","custom"}
VISIBILITY={"secret","discovered","admin"}
AVAILABILITY={"usable","blocked","approval"}


def endpoint(conn,endpoint_id,campaign_id):
    row=conn.execute("SELECT t.* FROM map_transitions t JOIN maps m ON m.id=t.map_id WHERE t.id=? AND m.campaign_id=?",(endpoint_id,campaign_id)).fetchone()
    if row is None: raise ValueError("Passage endpoint not found in this campaign.")
    return row


def effective(row):
    result=dict(row)
    result["current_visibility"]=row["runtime_visibility"] or row["visibility"]
    result["current_availability"]=row["runtime_availability"] or row["availability"]
    result["broken"]=bool(row["link_defined"] and not row["destination_id"])
    return result


def overview(conn,campaign_id):
    return [effective(r) for r in conn.execute(
        "SELECT t.*,m.name AS map_name,d.map_id AS destination_map_id,d.name AS destination_name FROM map_transitions t JOIN maps m ON m.id=t.map_id LEFT JOIN map_transitions d ON d.id=t.destination_id WHERE m.campaign_id=? ORDER BY m.id,t.name,t.id",(campaign_id,))]


def save(conn,campaign_id,map_id,data,endpoint_id=None,revision=None,return_link=False):
    m=maps.get(conn,map_id)
    if m is None or m["campaign_id"]!=campaign_id: raise ValueError("Map does not belong to this campaign.")
    old=endpoint(conn,endpoint_id,campaign_id) if endpoint_id else None
    if old is not None and (old["map_id"]!=map_id or old["revision"]!=revision): raise ValueError("Endpoint changed. Reload before saving.")
    name=data["name"].strip()
    if not name or len(name)>120 or len(data["player_label"])>120 or len(data["notes"])>2000: raise ValueError("Invalid endpoint name, label or notes length.")
    if data["kind"] not in KINDS or data["visibility"] not in VISIBILITY or data["availability"] not in AVAILABILITY or data["arrival"] not in ("area","preserve"): raise ValueError("Invalid endpoint configuration.")
    if not all(math.isfinite(data[k]) for k in ("x","y")) or not (0<=data["x"]<m["width"] and 0<=data["y"]<m["height"]): raise ValueError("Endpoint must be inside the map image.")
    dest=data.get("destination_id")
    target=endpoint(conn,dest,campaign_id) if dest else None
    if target is not None and target["map_id"]==map_id: raise ValueError("Choose an endpoint on another map.")
    if return_link and target is None: raise ValueError("A destination is required for a return connection.")
    if return_link and target["destination_id"] not in (None,endpoint_id): raise ValueError("Destination already has an outgoing connection; edit it explicitly instead.")
    values=(name,data["player_label"],data["kind"],data["x"],data["y"],data["visibility"],data["availability"],dest,int(bool(dest)),data["arrival"],data["notes"])
    if old is None:
        endpoint_id=uuid.uuid4().hex
        conn.execute("INSERT INTO map_transitions(id,map_id,name,player_label,kind,x,y,visibility,availability,destination_id,link_defined,arrival,notes) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",(endpoint_id,map_id,*values))
    else:
        conn.execute("UPDATE map_transitions SET name=?,player_label=?,kind=?,x=?,y=?,visibility=?,availability=?,destination_id=?,link_defined=?,arrival=?,notes=?,revision=revision+1 WHERE id=?",(*values,endpoint_id))
    if return_link: conn.execute("UPDATE map_transitions SET destination_id=?,link_defined=1,revision=revision+1 WHERE id=?",(endpoint_id,dest))
    return effective(endpoint(conn,endpoint_id,campaign_id))


def runtime(conn,campaign_id,endpoint_id,revision,visibility,availability):
    row=endpoint(conn,endpoint_id,campaign_id)
    if row["revision"]!=revision: raise ValueError("Endpoint changed. Reload first.")
    if (visibility is not None and visibility not in VISIBILITY) or (availability is not None and availability not in AVAILABILITY): raise ValueError("Invalid runtime state.")
    conn.execute("UPDATE map_transitions SET runtime_visibility=?,runtime_availability=?,revision=revision+1 WHERE id=?",(visibility,availability,endpoint_id))
    return effective(endpoint(conn,endpoint_id,campaign_id))


def reset_runtime(conn,map_id):
    conn.execute("UPDATE map_transitions SET runtime_visibility=NULL,runtime_availability=NULL,revision=revision+1 WHERE map_id=? AND (runtime_visibility IS NOT NULL OR runtime_availability IS NOT NULL)",(map_id,))


def arrival_info(conn,ctx,campaign_id,source_id):
    from .fog import MapSpec
    from .wall_type_settings import boundary_segments,disabled_for_map
    from ..repositories import walls
    source=endpoint(conn,source_id,campaign_id)
    if not source["destination_id"]: raise ValueError("Passage has no destination (or its destination was deleted).")
    target=endpoint(conn,source["destination_id"],campaign_id)
    source_map,target_map=maps.get(conn,source["map_id"]),maps.get(conn,target["map_id"])
    for row,m in ((source,source_map),(target,target_map)):
        if not (0<=row["x"]<m["width"] and 0<=row["y"]<m["height"]): raise ValueError("Endpoint lies outside its current map image. Reposition it first.")
    spec=MapSpec.from_row(target_map,ctx.settings.maps_dir)
    segs=boundary_segments(walls.list_for_map(conn,target["map_id"]),disabled_for_map(conn,target_map))
    current=effective(source)
    info=dict(source_revision=source["revision"],destination_revision=target["revision"],destination_id=target["id"],
        destination_map_id=target["map_id"],destination_name=target["name"],destination_map_name=target_map["name"],arrival=source["arrival"],
        destination_version=[spec.cache_token,spec.walls_version,spec.fog_version],
        needs_override=current["current_availability"]!="usable" or current["current_visibility"]=="secret",
        source_state=current["current_availability"],source_visibility=current["current_visibility"],fraction=0.,warning=False)
    if source["arrival"]=="area":
        area=ctx.fog.area_map(spec,segs)
        res=ctx.fog.describe_click(area,target["x"],target["y"])
        px,py=int(target["x"]*area.scale),int(target["y"]*area.scale)
        if not res.label or not int(area.labels[py,px]): raise ValueError("Arrival endpoint is on a wall. Move it or use Preserve destination fog.")
        info.update(fraction=res.fraction,warning=bool(res.leak_warning or not segs or res.fraction>=.5))
    return source,target,info


def travel(conn,ctx,campaign_id,user_id,data):
    """Execute under BEGIN IMMEDIATE; replay of identical input does not mutate state."""
    encoded=json.dumps(data,sort_keys=True,separators=(",",":"))
    prior=conn.execute("SELECT request_json,result_json FROM map_transition_travel WHERE campaign_id=? AND user_id=? AND request_id=?",(campaign_id,user_id,data["request_id"])).fetchone()
    if prior:
        if prior["request_json"]!=encoded: raise ValueError("Travel request ID already used for different input.")
        return json.loads(prior["result_json"])
    campaign=campaigns.get(conn,campaign_id)
    if campaign["active_map_id"]!=data["expected_active_map_id"]: raise ValueError("Active map changed. Reload before travelling.")
    source,target,info=arrival_info(conn,ctx,campaign_id,data["source_endpoint_id"])
    if source["map_id"]!=campaign["active_map_id"]: raise ValueError("Show the source map to players before travelling.")
    if any(data[k]!=info[k] for k in ("source_revision","destination_revision","destination_version")): raise ValueError("Passage or destination changed. Preview travel again.")
    if info["needs_override"] and not data["override"]: raise ValueError("Secret, blocked or approval-required passage needs explicit DM approval.")
    if info["warning"] and not data["allow_large_reveal"]: raise ValueError("Arrival may reveal a large area. Explicit confirmation is required.")
    checkpoint(conn,source["map_id"])
    if source["arrival"]=="area": fog_ops.add(conn,target["map_id"],"reveal",target["x"],target["y"],user_id)
    maps.bump_fog(conn,target["map_id"])
    checkpoint(conn,target["map_id"])
    campaigns.set_active_map(conn,campaign_id,target["map_id"])
    result=dict(ok=True,active_map_id=target["map_id"],admin_url=f"/maps/{target['map_id']}")
    conn.execute("INSERT INTO map_transition_travel VALUES(?,?,?,?,?)",(campaign_id,user_id,data["request_id"],encoded,json.dumps(result)))
    return result


def viewer_markers(conn,map_id):
    return tuple((r["x"],r["y"],r["kind"],r["player_label"]) for r in conn.execute("SELECT x,y,kind,player_label FROM map_transitions WHERE map_id=? AND COALESCE(runtime_visibility,visibility)='discovered' ORDER BY id",(map_id,)))


def marker_overlay(engine,spec,segs,ops,size):
    from PIL import Image,ImageDraw,ImageFont
    import numpy as np
    layer=Image.new("RGBA",size)
    if not spec.viewer_transition_markers: return layer
    mask=engine.mask(spec,segs,ops)
    area=engine.area_map(spec,segs)
    revealed=engine.revealed_labels(area,ops)
    draw=ImageDraw.Draw(layer)
    font=ImageFont.load_default()
    for path in ("C:/Windows/Fonts/arial.ttf","/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        try: font=ImageFont.truetype(path,12);break
        except OSError: pass
    codes=dict(stairs="S",ladder="L",hole="H",portal="P",climb="C",custom="X")
    for x,y,kind,label in spec.transition_markers:
        if not (0<=x<spec.width and 0<=y<spec.height): continue
        if int(area.labels[int(y*area.scale),int(x*area.scale)]) not in revealed: continue
        px,py=x*size[0]/spec.width,y*size[1]/spec.height
        draw.ellipse((px-10,py-10,px+10,py+10),fill="#172d46",outline="white",width=2)
        draw.text((px,py),codes[kind],font=font,fill="white",anchor="mm")
        if spec.viewer_transition_labels and label:
            try:
                box=draw.textbbox((px+14,py-7),label,font=font)
                draw.rectangle((box[0]-3,box[1]-2,box[2]+3,box[3]+2),fill=(0,0,0,200))
                draw.text((px+14,py-7),label,font=font,fill="white")
            except UnicodeEncodeError: pass
    pixels=np.array(layer)
    visible=np.array(Image.fromarray((mask*255).astype(np.uint8)).resize(size,Image.Resampling.NEAREST))>0
    pixels[~visible,3]=0
    return Image.fromarray(pixels)

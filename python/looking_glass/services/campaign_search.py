"""Literal, Unicode-aware campaign search. No writes or player actions."""
from urllib.parse import urlencode
KINDS = ("all", "map", "room", "passage", "library")
MAX_QUERY = 200
MAX_RESULTS = 50


def target_url(cid, mid, kind="map", key=""):
    url=f"/campaigns/{cid}/inspect/maps/{mid}"
    return url+("?"+urlencode({"kind":kind,"key":str(key)}) if kind!="map" else "")


def excerpt(text, words, length=220):
    text=" ".join(text.split())
    start=0
    for i in range(0,len(text),length//2):
        if any(w in text[i:i+length].casefold() for w in words):
            start=max(0,i-30);break
    return ("…" if start else "")+text[start:start+length]+("…" if start+length<len(text) else "")


def candidates(conn,cid):
    for row in conn.execute("SELECT id,name FROM maps WHERE campaign_id=? ORDER BY sort_order,id",(cid,)):
        yield dict(kind="map",key="",map_id=row["id"],map_name=row["name"],title=row["name"],text="")
    queries=(
        ("room","area_key","r.markdown","room_notes"),
        ("passage","id","r.player_label || ' ' || r.notes","map_transitions"),
        ("library","id","r.markdown","imported_room_notes"))
    for kind,key,text,table in queries:
        for row in conn.execute(f"SELECT r.{key} AS object_key,r.map_id,r.name,{text} AS body,m.name AS map_name FROM {table} r JOIN maps m ON m.id=r.map_id WHERE m.campaign_id=? ORDER BY m.sort_order,m.id,r.{key}",(cid,)):
            yield dict(kind=kind,key=row["object_key"],map_id=row["map_id"],map_name=row["map_name"],title=row["name"] or "Unnamed room note",text=row["body"])


def search_campaign(conn,cid,query="",kind="all",limit=MAX_RESULTS):
    if len(query)>MAX_QUERY or kind not in KINDS:
        raise ValueError("Invalid query or result type")
    query=" ".join(query.split());words=query.casefold().split()
    limit=max(1,min(int(limit),MAX_RESULTS));best=[]
    if words:
        for row in candidates(conn,cid):
            if kind!="all" and row["kind"]!=kind:continue
            title=row["title"].casefold()
            haystack=" ".join((title,row["map_name"].casefold(),row["text"].casefold()))
            if not all(w in haystack for w in words):continue
            rank=(0 if title==query.casefold() else 1 if title.startswith(query.casefold()) else 2 if all(w in title for w in words) else 3,row["map_name"].casefold(),title,row["kind"],str(row["key"]),row["map_id"])
            result={k:row[k] for k in ("kind","key","map_id","map_name","title")}
            result.update(snippet=excerpt(row["text"],words),url=target_url(cid,row["map_id"],row["kind"],row["key"]))
            best.append((rank,result));best.sort(key=lambda pair:pair[0]);del best[limit+1:]
    return dict(query=query,kind=kind,results=[r for _,r in best[:limit]],truncated=len(best)>limit,limit=limit)


def inspect_target(conn,mid,kind,key):
    if kind=="map":return None
    queries={"room":"SELECT name,markdown,x,y FROM room_notes WHERE map_id=? AND area_key=?",
             "passage":"SELECT name,notes AS markdown,x,y FROM map_transitions WHERE map_id=? AND id=?",
             "library":"SELECT name,markdown FROM imported_room_notes WHERE map_id=? AND id=?"}
    if kind not in queries:raise ValueError("Unknown navigation target")
    row=conn.execute(queries[kind],(mid,key)).fetchone()
    if row is None:raise LookupError("This result no longer exists on this map. Search again.")
    return {"kind":kind,**dict(row)}

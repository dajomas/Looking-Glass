import sqlite3
import json
from collections.abc import Iterable
from ..services.wall_model import WallSegment


def list_for_map(conn: sqlite3.Connection, map_id: int, *, designed: bool = False) -> list[WallSegment]:
    rows = conn.execute("SELECT w.id,w.x1,w.y1,w.x2,w.y2,w.kind,w.blocks,w.passage,r.kind AS runtime_kind "
                        "FROM walls w LEFT JOIN door_runtime_states r ON r.wall_id=w.id "
                        "WHERE w.map_id=? ORDER BY w.id", (map_id,)).fetchall()
    states = {}
    if not designed:
        for r in conn.execute("SELECT r.wall_id,r.side,r.kind FROM passage_runtime_states r JOIN walls w ON w.id=r.wall_id WHERE w.map_id=?", (map_id,)):
            states.setdefault(r["wall_id"], {})[str(r["side"])] = r["kind"]
    return [WallSegment(r["x1"],r["y1"],r["x2"],r["y2"],
                        r["kind"] if designed else (states.get(r["id"], {}).get("-1") or r["runtime_kind"] or r["kind"]), bool(r["blocks"]),
                        id=r["id"], designed_kind=r["kind"], passage=json.loads(r["passage"]), runtime=states.get(r["id"], {})) for r in rows]


def replace(conn: sqlite3.Connection, map_id: int, segments: Iterable[WallSegment]) -> int:
    from ..services.passages import validate_passages
    segments = validate_passages(list(segments))
    conn.execute("DELETE FROM walls WHERE map_id=?", (map_id,))
    rows = [(map_id,s.x1,s.y1,s.x2,s.y2,s.kind,int(s.blocks),json.dumps(s.passage)) for s in segments]
    conn.executemany("INSERT INTO walls(map_id,x1,y1,x2,y2,kind,blocks,passage) VALUES(?,?,?,?,?,?,?,?)", rows)
    return len(rows)


def clear(conn: sqlite3.Connection, map_id: int) -> None:
    conn.execute("DELETE FROM walls WHERE map_id=?", (map_id,))

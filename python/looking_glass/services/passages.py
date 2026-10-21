"""Validate authored passage graphs and manage independent runtime Entry states."""
import re
from collections import defaultdict

DOOR_KINDS = ("door", "locked_door", "unlocked_door")
ROLES = ("entry", "exit", "both", "none")


def validate_passages(segments):
    pairs = defaultdict(list)
    for s in segments:
        p = s.passage
        if not isinstance(p, dict):
            raise ValueError("Passage configuration must be an object.")
        if s.kind == "secret":
            if set(p) - {"after"} or p.get("after", "door") not in DOOR_KINDS:
                raise ValueError("Secret door: choose a valid post-discovery type.")
        elif s.kind == "portal":
            if set(p) != {"pair", "end", "sides"} or not isinstance(p.get("pair"), str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", p["pair"]):
                raise ValueError("Portal: configure a pair before saving/exporting.")
            if p["end"] not in ("a", "b") or not isinstance(p["sides"], list) or len(p["sides"]) != 2:
                raise ValueError("Portal: expected end a/b and two sides.")
            for side in p["sides"]:
                if not isinstance(side, dict) or set(side) - {"role","kind","after","exit"} or side.get("role") not in ROLES:
                    raise ValueError("Portal: invalid side role.")
                if side["role"] in ("entry","both"):
                    if side.get("kind") not in (*DOOR_KINDS, "secret") or side.get("after", "door") not in DOOR_KINDS:
                        raise ValueError("Portal entry: invalid initial/post-discovery type.")
                    if type(side.get("exit")) is not int or side["exit"] not in (0,1):
                        raise ValueError("Every Entry needs one destination side on the other element.")
                elif set(side) != {"role"}:
                    raise ValueError("Exit/None sides cannot carry entry state or routing.")
            if sum(v["role"] == "none" for v in p["sides"]) > 1:
                raise ValueError("Each portal element may have at most one None side.")
            if not s.blocks:
                raise ValueError("Portal elements must be authored as blocking segments.")
            pairs[p["pair"]].append(s)
        elif p:
            raise ValueError("Only secret doors and portals accept passage configuration.")
    for group in pairs.values():
        if len(group) != 2 or {s.passage["end"] for s in group} != {"a","b"}:
            raise ValueError("A portal pair must contain exactly two elements, ends a and b.")
        used = set()
        entries = 0
        for s in group:
            other = next(t for t in group if t is not s)
            for side in s.passage["sides"]:
                if side["role"] not in ("entry","both"):
                    continue
                entries += 1
                dest = side["exit"]
                if other.passage["sides"][dest]["role"] not in ("exit","both"):
                    raise ValueError("An Entry must target an Exit/Both side on the other element.")
                used.add((other.passage["end"], dest))
        if not entries:
            raise ValueError("A portal pair needs at least one Entry and one Exit.")
        for s in group:
            for i, side in enumerate(s.passage["sides"]):
                if side["role"] in ("exit","both") and (s.passage["end"], i) not in used:
                    raise ValueError("Every Exit must have at least one incoming Entry.")
    return segments


def entry_kind(seg, side=-1):
    if side == -1:
        return seg.kind
    return seg.runtime.get(str(side), seg.passage["sides"][side].get("kind", "door"))


def set_state(conn, map_id, wall, side, kind):
    if kind not in DOOR_KINDS:
        raise ValueError("Invalid passage state.")
    conn.execute("INSERT INTO passage_runtime_states(wall_id,side,kind) VALUES(?,?,?) "
                 "ON CONFLICT(wall_id,side) DO UPDATE SET kind=excluded.kind", (wall.id,side,kind))
    conn.execute("UPDATE maps SET walls_version=walls_version+1,fog_version=fog_version+1 WHERE id=?", (map_id,))


def reset(conn, map_id):
    changed = conn.execute("SELECT 1 FROM passage_runtime_states r JOIN walls w ON w.id=r.wall_id WHERE w.map_id=? LIMIT 1", (map_id,)).fetchone()
    conn.execute("DELETE FROM passage_runtime_states WHERE wall_id IN (SELECT id FROM walls WHERE map_id=?)", (map_id,))
    if changed:
        conn.execute("UPDATE maps SET walls_version=walls_version+1 WHERE id=?", (map_id,))

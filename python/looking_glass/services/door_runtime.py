"""Authored wall types are immutable during play; runtime state is an override."""
MANAGED_DOORS = frozenset({"locked_door", "unlocked_door"})


def set_kind(conn, map_id, wall_id, kind):
    if kind not in MANAGED_DOORS:
        raise ValueError("Invalid runtime door type.")
    wall = conn.execute("SELECT kind FROM walls WHERE id=? AND map_id=?", (wall_id,map_id)).fetchone()
    if wall is None or wall["kind"] not in MANAGED_DOORS:
        raise ValueError("Not an authored locked/unlocked door on this map.")
    if wall["kind"] == kind:
        conn.execute("DELETE FROM door_runtime_states WHERE wall_id=?", (wall_id,))
    else:
        conn.execute("INSERT INTO door_runtime_states(wall_id,kind) VALUES(?,?) "
                     "ON CONFLICT(wall_id) DO UPDATE SET kind=excluded.kind", (wall_id,kind))
    conn.execute("UPDATE maps SET walls_version=walls_version+1, fog_version=fog_version+1 WHERE id=?", (map_id,))


def reset(conn, map_id):
    changed = conn.execute("SELECT 1 FROM door_runtime_states r JOIN walls w ON w.id=r.wall_id WHERE w.map_id=? LIMIT 1", (map_id,)).fetchone()
    conn.execute("DELETE FROM door_runtime_states WHERE wall_id IN (SELECT id FROM walls WHERE map_id=?)", (map_id,))
    if changed:
        conn.execute("UPDATE maps SET walls_version=walls_version+1 WHERE id=?", (map_id,))


def decide(kind, gesture, hit):
    if kind == "locked_door":
        return "unlock" if gesture == "double" and hit == "arrow" else "none"
    if kind == "unlocked_door" and gesture == "double":
        return "lock"
    return "reveal"

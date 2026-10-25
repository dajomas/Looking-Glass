"""Split Markdown by its highest document-level heading, preserving section source."""
import hashlib
import html
import mistune

MAX_BYTES = 1024 * 1024

class ImportError(ValueError):
    pass

class _Headings(mistune.BlockParser):
    def parse_atx_heading(self, match, state):
        end = super().parse_atx_heading(match, state)
        if state.parent is None:
            token = state.last_token()
            state.env.setdefault("room_headings", []).append((match.start(), end, token["attrs"]["level"], token["text"]))
        return end

    def parse_setex_heading(self, match, state):
        last = state.last_token()
        start = state.cursor - len(last["text"]) if last and last["type"] == "paragraph" else None
        end = super().parse_setex_heading(match, state)
        if end and start is not None and state.parent is None:
            token = state.last_token()
            state.env.setdefault("room_headings", []).append((start, end, token["attrs"]["level"], token["text"]))
        return end


def _plain(tokens):
    return "".join(" " if t["type"] in ("softbreak", "linebreak") else _plain(t["children"]) if "children" in t else
                   t.get("raw", "") if t["type"] not in ("inline_html",) else "" for t in tokens)


def parse(raw):
    if len(raw) > MAX_BYTES:
        raise ImportError("Markdown import exceeds 1 MiB.")
    try:
        source = raw.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    except UnicodeDecodeError as exc:
        raise ImportError("Use a UTF-8 Markdown file.") from exc
    if "\x00" in source:
        raise ImportError("Markdown must not contain NUL characters.")
    if not source.endswith("\n"):
        source += "\n"
    state = mistune.BlockState()
    state.process(source)
    _Headings().parse(state)
    headings = state.env.get("room_headings", [])
    if not headings:
        raise ImportError("No document-level Markdown headings found.")
    level = min(h[2] for h in headings)
    headings = [h for h in headings if h[2] == level]
    if len(headings) > 500:
        raise ImportError("Import at most 500 room sections per file.")
    entries = []
    inline = mistune.InlineParser()
    for index, (start, end, _, title) in enumerate(headings):
        name = html.unescape(_plain(inline(title.strip(), {"ref_links": {}}))).strip()
        note = source[end:headings[index+1][0] if index+1 < len(headings) else len(source)].strip("\n")
        if not name or len(name) > 200:
            raise ImportError("Every room heading must have a name of 1–200 characters.")
        if len(note) > 100000:
            raise ImportError(f"Room '{name}' exceeds the 100,000-character note limit.")
        digest = hashlib.sha256((name + "\0" + note).encode()).hexdigest()
        entries.append({"name": name, "markdown": note, "digest": digest})
    return {"level": level, "ignored_preamble": bool(source[:headings[0][0]].strip()), "entries": entries}


def store(conn, map_id, entries):
    added = 0
    for entry in entries:
        added += conn.execute("""INSERT OR IGNORE INTO imported_room_notes(map_id,name,markdown,digest)
            VALUES(?,?,?,?)""", (map_id, entry["name"], entry["markdown"], entry["digest"])).rowcount
    return added


def name_key(name):
    return name.strip().casefold()


def list_entries(conn, map_id):
    rooms = list(conn.execute("SELECT name,markdown FROM room_notes WHERE map_id=?", (map_id,)))
    assigned = {name_key(row["name"]) for row in rooms if row["name"].strip()}
    result = []
    for row in conn.execute(
            "SELECT id,name,markdown FROM imported_room_notes WHERE map_id=? ORDER BY name,id", (map_id,)):
        entry = dict(row)
        entry["assigned"] = name_key(entry["name"]) in assigned
        entry["notes_match"] = any(name_key(row["name"]) == name_key(entry["name"])
            and row["markdown"].replace("\r\n", "\n") == entry["markdown"].replace("\r\n", "\n") for row in rooms)
        result.append(entry)
    return result


def delete_unassigned(conn, map_id, entry_id):
    """Caller holds an IMMEDIATE transaction across assignment check and delete."""
    row = conn.execute("SELECT name FROM imported_room_notes WHERE map_id=? AND id=?", (map_id,entry_id)).fetchone()
    if row is None:
        raise ImportError("Imported entry not found on this map.")
    key = name_key(row["name"])
    if any(name_key(r["name"]) == key for r in conn.execute("SELECT name FROM room_notes WHERE map_id=?", (map_id,))):
        raise ImportError("This imported room name is assigned. Clear or rename its room before deleting the entry.")
    conn.execute("DELETE FROM imported_room_notes WHERE map_id=? AND id=?", (map_id,entry_id))

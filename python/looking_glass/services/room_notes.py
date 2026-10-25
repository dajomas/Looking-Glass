"""Conservative geometry identity and safe, admin-only Markdown rendering."""
import hashlib
import numpy as np
import mistune
import bleach

_markdown = mistune.create_markdown(escape=True, plugins=["table", "strikethrough"])

def render(text):
    return bleach.clean(_markdown(text), tags={
        "p", "br", "hr", "h1", "h2", "h3", "h4", "h5", "h6", "strong", "em",
        "del", "blockquote", "ul", "ol", "li", "pre", "code", "a",
        "table", "thead", "tbody", "tr", "th", "td"},
        attributes={"a": ["href", "title"]}, protocols={"https", "http", "mailto"}, strip=True)

def area_key(area, label, width, height):
    cached = area.region_signatures.get(("notes", label, width, height))
    if cached:
        return cached
    mask = area.labels == label
    key = hashlib.sha256(repr((width, height, area.shape, area.scale)).encode()
                         + np.packbits(mask).tobytes()).hexdigest()
    area.region_signatures[("notes", label, width, height)] = key
    return key

def payload(conn, map_id, key, revealed):
    row = conn.execute("SELECT * FROM room_notes WHERE map_id=? AND area_key=?", (map_id, key)).fetchone()
    return {"area_key": key, "revealed": revealed, "name": row["name"] if row else "",
            "markdown": row["markdown"] if row else "", "revision": row["revision"] if row else 0,
            "html": render(row["markdown"]) if row else ""}

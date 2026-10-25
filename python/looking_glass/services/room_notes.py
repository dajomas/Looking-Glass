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


def edit_mask_png(area, label):
    """Independent admin decoration; never updates fog masks or operations."""
    import io
    from PIL import Image
    from scipy import ndimage
    mask = area.labels == label
    edge = mask & ~ndimage.binary_erosion(mask, iterations=2, border_value=0)
    rgba = np.zeros((*mask.shape, 4), dtype=np.uint8)
    rgba[mask] = (255, 193, 7, 75)
    rgba[edge] = (255, 193, 7, 245)
    out = io.BytesIO()
    Image.fromarray(rgba).save(out, "PNG")
    return out.getvalue()


def name_status_png(area, rows, width, height):
    """Color current areas by saved, geometry-matched names, independent of fog."""
    import io
    from PIL import Image
    named = set()
    h, w = area.labels.shape
    for row in rows:
        if not row["name"].strip() or not (0 <= row["x"] < width and 0 <= row["y"] < height):
            continue
        px, py = int(row["x"] * area.scale), int(row["y"] * area.scale)
        if px >= w or py >= h:
            continue
        label = int(area.labels[py, px])
        if label and area_key(area, label, width, height) == row["area_key"]:
            named.add(label)
    palette = np.zeros((area.count + 1, 4), dtype=np.uint8)
    palette[1:] = (231, 76, 60, 90)
    for label in named:
        palette[label] = (46, 204, 113, 90)
    rgba = palette[area.labels]
    out = io.BytesIO()
    Image.fromarray(rgba).save(out, "PNG")
    return out.getvalue(), len(named), area.count - len(named)

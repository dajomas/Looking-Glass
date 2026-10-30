"""Shared test data builders; no pytest fixtures or application imports."""
import io

from PIL import Image


def two_room_scene(width=400, height=200, padding=0.25, grid=100, door=False) -> dict:
    """Two rooms side by side separated by a vertical wall at x=200 (image coords)."""
    pad_x = -(-width * padding // grid) * grid
    pad_y = -(-height * padding // grid) * grid
    def w(x1, y1, x2, y2, **kw):
        return {"c": [x1 + pad_x, y1 + pad_y, x2 + pad_x, y2 + pad_y], "move": 20, "sight": 20, **kw}
    walls = [w(10, 10, 390, 10), w(390, 10, 390, 190), w(390, 190, 10, 190), w(10, 190, 10, 10)]
    if door:
        walls += [w(200, 10, 200, 80), w(200, 120, 200, 190), w(200, 80, 200, 120, door=1)]
    else:
        walls.append(w(200, 10, 200, 190))
    return {"name": "Test scene", "width": width, "height": height, "padding": padding,
            "grid": {"size": grid}, "background": {"offsetX": 0, "offsetY": 0}, "walls": walls}


def png_bytes(w=400, h=200, color=(200, 30, 30)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (w, h), color).save(buf, "PNG")
    return buf.getvalue()

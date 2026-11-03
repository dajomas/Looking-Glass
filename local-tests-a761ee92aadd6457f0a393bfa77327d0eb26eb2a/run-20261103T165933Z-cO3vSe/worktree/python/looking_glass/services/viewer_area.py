"""Read-only framing of one currently revealed component; no hidden geometry payloads."""
import math
import numpy as np
from scipy import ndimage
from .reveal_bounds import revealed_bounds


def revealed_area_bounds(engine, spec, segments, ops, x, y):
    if not (math.isfinite(x) and math.isfinite(y) and 0 <= x < spec.width and 0 <= y < spec.height):
        return None
    area = engine.area_map(spec, segments)
    mask = engine.mask(spec, segments, ops)
    h, w = area.shape
    # Viewer imagery stretches the work mask to the full image; include ceil-rounding.
    px, py = min(w-1, int(x*w/spec.width)), min(h-1, int(y*h/spec.height))
    if not mask[py, px]:
        return None
    revealed = engine.revealed_labels(area, ops)
    label = int(area.labels[py, px])
    if label == 0:
        # Visible boundary pixels may snap only to a revealed open label.
        radius = engine.thickness * 3
        y0, y1 = max(0, py-radius), min(h, py+radius+1)
        x0, x1 = max(0, px-radius), min(w, px+radius+1)
        window = area.labels[y0:y1, x0:x1]
        ys, xs = np.nonzero(np.isin(window, list(revealed)))
        if not len(xs):
            return None
        i = int(np.argmin((ys+y0-py)**2+(xs+x0-px)**2))
        label = int(window[ys[i], xs[i]])
    if label not in revealed:
        return None
    room = area.labels == label
    room = ndimage.binary_dilation(room, iterations=engine.thickness) & mask
    return revealed_bounds(room, spec.width, spec.height)

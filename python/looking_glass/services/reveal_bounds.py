"""Bounds of revealed pixels only; never includes hidden geometry."""
import numpy as np


def revealed_bounds(mask, image_width, image_height):
    ys, xs = np.nonzero(mask)
    if not len(xs):
        return None
    height, width = mask.shape
    sx, sy = image_width / width, image_height / height
    return {"x": float(xs.min() * sx), "y": float(ys.min() * sy),
            "width": float((xs.max() - xs.min() + 1) * sx),
            "height": float((ys.max() - ys.min() + 1) * sy)}

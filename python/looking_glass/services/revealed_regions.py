"""Stable opaque fingerprints for currently revealed areas, never hidden labels/geometry."""
import hashlib
import json
import numpy as np
from scipy import ndimage


def revealed_area_signatures(engine, spec, segments, ops):
    area = engine.area_map(spec, segments)
    revealed = engine.revealed_labels(area, ops)
    if not revealed:
        return []
    result = []
    # Cached with the AreaMap lifetime/LRU; use its map lock for concurrent state requests.
    with engine._lock(spec.id):
        if area.region_slices is None:
            area.region_slices = ndimage.find_objects(area.labels, max_label=area.count)
        for label in sorted(revealed):
            key = (label, spec.width, spec.height)
            signature = area.region_signatures.get(key)
            if signature is None:
                region = area.region_slices[label-1]
                if region is None:
                    continue
                y, x = region
                # The footprint contains this revealed component only; no numeric labels are hashed.
                header = json.dumps([spec.width, spec.height, *area.shape,
                                     y.start,y.stop,x.start,x.stop], separators=(",",":")).encode()
                footprint = np.packbits(area.labels[region] == label).tobytes()
                signature = hashlib.sha256(header + b"\0" + footprint).hexdigest()
                area.region_signatures[key] = signature
            result.append(signature)
    return sorted(result)

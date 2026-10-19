"""Known importer categories and non-destructive per-map fog filtering."""
import json
from dataclasses import replace

WALL_TYPES = ("wall", "door", "locked_door", "unlocked_door", "secret", "window", "invisible", "ethereal")


def disabled_types(row):
    return json.loads(row["disabled_wall_types"])


def filter_segments(segments, disabled):
    return [replace(s, blocks=False) if (s.designed_kind or s.kind) in disabled else s for s in segments]

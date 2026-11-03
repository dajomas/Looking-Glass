import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from looking_glass.config import load_settings  # noqa: E402
from looking_glass_test_helpers import png_bytes, two_room_scene  # noqa: E402,F401


@pytest.fixture
def settings(tmp_path):
    return load_settings(overrides={
        "storage": {"data_dir": str(tmp_path / "data")},
        "fog": {"work_max_dim": 400, "feather_px": 0},
        "viewer": {"image_format": "png"},
    })


@pytest.fixture
def scene_json() -> bytes:
    return json.dumps(two_room_scene()).encode()

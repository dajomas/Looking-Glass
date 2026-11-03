"""Bug 4: capture composite bytes under the existing map lock."""
import io
import threading
from dataclasses import replace
from pathlib import Path

import pytest
from PIL import Image
from looking_glass.config import DEFAULTS
from looking_glass.services.fog import FogEngine, MapSpec
from looking_glass.services.wall_model import Calibration, FogOp, WallSegment


def setup(tmp_path, fmt="png"):
    engine = FogEngine(dict(DEFAULTS["fog"], work_max_dim=80, feather_px=2),
        dict(DEFAULTS["viewer"], max_image_dim=80, image_format=fmt), tmp_path/"cache")
    path = tmp_path/"map.png"
    Image.new("RGB", (80,40), (230,20,20)).save(path)
    spec = MapSpec(1,80,40,path,Calibration(),True,1,1,cache_token="one",
                   door_arrows_enabled=False,viewer_door_arrows_enabled=False)
    return engine, spec, [WallSegment(40,0,40,39)], [FogOp("reveal",20,20)]


@pytest.mark.parametrize("fmt,expected", [("png","PNG"),("jpeg","JPEG"),("webp","WEBP")])
def test_bytes_survive_new_render_and_invalidation(tmp_path, fmt, expected):
    engine, spec, walls, ops = setup(tmp_path,fmt)
    body = engine.viewer_bytes(spec,walls,ops)
    cached = engine.viewer_image(spec,walls,ops)
    assert body == cached.read_bytes()
    engine.viewer_image(replace(spec,fog_version=2),walls,[])
    assert not cached.exists()
    engine.invalidate(spec.id)
    with Image.open(io.BytesIO(body)) as image:
        assert image.size == (80,40) and image.format == expected
        assert image.convert("RGB").getpixel((20,20))[0] > 150


@pytest.mark.parametrize("warm", [False,True])
@pytest.mark.parametrize("cleanup", ["invalidate","render"])
def test_capture_holds_map_lock_during_read(tmp_path, monkeypatch, warm, cleanup):
    engine, spec, walls, ops = setup(tmp_path)
    if warm:
        engine.viewer_image(spec,walls,ops)
    reading, release, finished = threading.Event(), threading.Event(), threading.Event()
    original = Path.read_bytes
    results, errors = [], []
    def read(path):
        if path.parent == engine.cache_dir and path.name.startswith("viewer_"):
            reading.set()
            assert release.wait(5), "read barrier timed out"
        return original(path)
    monkeypatch.setattr(Path,"read_bytes",read)
    def capture():
        try:
            results.append(engine.viewer_bytes(spec,walls,ops))
        except BaseException as error:
            errors.append(error)
    def prune():
        try:
            if cleanup == "invalidate":
                engine.invalidate(spec.id)
            else:
                engine.viewer_image(replace(spec,fog_version=2),walls,[])
            finished.set()
        except BaseException as error:
            errors.append(error)
    reader = threading.Thread(target=capture, daemon=True)
    cleaner = None
    reader.start()
    try:
        assert reading.wait(5)
        acquired = engine._lock(spec.id).acquire(blocking=False)
        if acquired:
            engine._lock(spec.id).release()
        assert not acquired, "read escaped the per-map lock"
        cleaner = threading.Thread(target=prune, daemon=True)
        cleaner.start()
    finally:
        release.set()
        reader.join(5)
        if cleaner:
            cleaner.join(5)
    assert not reader.is_alive() and not errors and finished.is_set()
    with Image.open(io.BytesIO(results[0])) as image:
        assert image.size == (80,40)
        assert image.convert("RGB").getpixel((20,20))[0] > 150


def test_read_failure_releases_map_lock(tmp_path, monkeypatch):
    engine, spec, walls, ops = setup(tmp_path)
    engine.viewer_image(spec,walls,ops)
    def fail(path):
        raise OSError("injected read failure")
    monkeypatch.setattr(Path,"read_bytes",fail)
    with pytest.raises(OSError,match="injected"):
        engine.viewer_bytes(spec,walls,ops)
    finished = threading.Event()
    worker = threading.Thread(target=lambda:(engine.invalidate(spec.id),finished.set()), daemon=True)
    worker.start()
    worker.join(5)
    assert finished.is_set() and not worker.is_alive()


def test_unrelated_map_is_not_blocked(tmp_path):
    engine, spec, walls, ops = setup(tmp_path)
    results = []
    worker = threading.Thread(target=lambda:results.append(engine.viewer_bytes(
        replace(spec,id=2,cache_token="two"),walls,ops)), daemon=True)
    with engine._lock(spec.id):
        worker.start()
        worker.join(5)
    worker.join(5)
    assert not worker.is_alive() and results
    with Image.open(io.BytesIO(results[0])) as image:
        assert image.size == (80,40)

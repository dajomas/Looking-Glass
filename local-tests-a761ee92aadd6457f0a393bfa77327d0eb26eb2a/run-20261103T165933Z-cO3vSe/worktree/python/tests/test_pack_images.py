import base64
import io
import json
import zipfile

import pytest
from PIL import Image

from conftest import two_room_scene, png_bytes
from looking_glass.services.foundry_import import parse_wall_file, WallImportError
from looking_glass.services.pack_images import image_bytes
from looking_glass.services.images import store_map_image


def pack(files):
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        for name, value in files.items():
            z.writestr(name, value)
    return out.getvalue()


def test_foundry_image_and_thumbnail():
    art = png_bytes()
    uri = "data:image/png;base64," + base64.b64encode(art).decode()
    for key in ("img", "background"):
        scene = two_room_scene()
        scene[key] = {"src": uri} if key == "background" else uri
        ws = parse_wall_file(json.dumps(scene).encode())[0]
        assert image_bytes(ws) == art and not ws.image_is_thumbnail
    scene = dict(two_room_scene(), img="modules/example/map.png", thumb=uri)
    ws = parse_wall_file(json.dumps(scene).encode())[0]
    assert ws.image_is_thumbnail and ws.image_reference == "modules/example/map.png"
    assert image_bytes(ws) == art


def test_uvtt_embedded_image():
    art = png_bytes()
    data = {"resolution": {"pixels_per_grid": 100},
            "line_of_sight": [[{"x": 0,"y": 0},{"x": 1,"y": 0}]],
            "image": base64.b64encode(art).decode()}
    assert image_bytes(parse_wall_file(json.dumps(data).encode())[0]) == art


def test_zip_asset_overrides_thumbnail_and_decodes_path():
    scene = dict(two_room_scene(), img="art/full%20map.png",
                 thumb="data:image/png;base64,eA==")
    art = png_bytes(800, 400)
    raw = pack({"scenes/scene.json": json.dumps(scene), "scenes/art/full map.png": art})
    ws = parse_wall_file(raw, "pack.zip")[0]
    assert image_bytes(ws) == art and not ws.image_is_thumbnail


@pytest.mark.parametrize("name", ["../x.json", "/x.json", "C:/x.json", "a/../../x.json"])
def test_zip_unsafe_paths(name):
    with pytest.raises(WallImportError):
        parse_wall_file(pack({name: json.dumps(two_room_scene())}), "pack.zip")


def test_reference_only_never_reads_or_fetches():
    for ref in ("http://localhost/private.png", "/etc/passwd", "modules/map.png"):
        ws = parse_wall_file(json.dumps(dict(two_room_scene(), img=ref)).encode())[0]
        assert not ws.image_data
        with pytest.raises(WallImportError):
            image_bytes(ws)


def test_bad_base64_and_size_limit():
    ws = parse_wall_file(json.dumps(two_room_scene()).encode())[0]
    ws.image_data = "%%%"
    with pytest.raises(WallImportError): image_bytes(ws)
    ws.image_data = base64.b64encode(b"0123456789").decode()
    with pytest.raises(WallImportError): image_bytes(ws, 4)


def test_normalization_static_png(tmp_path):
    frames = [Image.new("RGB", (20,10), color) for color in ("red", "blue")]
    out = io.BytesIO()
    frames[0].save(out, "GIF", save_all=True, append_images=frames[1:])
    stored = store_map_image(out.getvalue(), tmp_path, 1)
    with Image.open(tmp_path / stored.relative_path) as art:
        assert art.format == "PNG" and getattr(art, "n_frames", 1) == 1
        assert art.getpixel((5,5)) == (255,0,0)

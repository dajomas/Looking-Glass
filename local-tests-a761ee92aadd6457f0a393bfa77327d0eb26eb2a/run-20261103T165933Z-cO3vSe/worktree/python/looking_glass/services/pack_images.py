"""Bounded embedded-image / ZIP handling. Never fetch URLs or read host paths."""
import base64
import binascii
import io
import posixpath
import zipfile
from urllib.parse import unquote

from .foundry_import import WallImportError

MAX_PACK_BYTES = 150 * 1024 * 1024
MAX_ENTRIES = 2000


def image_bytes(ws, limit=MAX_PACK_BYTES):
    value = ws.image_data
    if not value:
        raise WallImportError("This wall set contains no embedded image. Upload the referenced artwork instead.")
    if value.startswith("data:"):
        header, sep, value = value.partition(",")
        if not sep or not header.startswith("data:image/") or not header.endswith(";base64"):
            raise WallImportError("Only base64 image data URIs are supported.")
    if len(value) > ((limit + 2) // 3) * 4 + 8:
        raise WallImportError("Embedded image exceeds the upload limit.")
    try:
        raw = base64.b64decode(value, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise WallImportError("Invalid base64 image data.") from exc
    if len(raw) > limit:
        raise WallImportError("Embedded image exceeds the upload limit.")
    return raw


def _safe_name(name):
    name = unquote(name).replace("\\", "/")
    if name.startswith("/") or ":" in name or ".." in name.split("/"):
        raise WallImportError("Unsafe path in wall pack.")
    return posixpath.normpath(name)


def parse_zip_pack(raw, parser):
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            entries = archive.infolist()
            if len(entries) > MAX_ENTRIES or sum(e.file_size for e in entries) > MAX_PACK_BYTES:
                raise WallImportError("Wall pack exceeds the expanded size or entry limit.")
            files = {}
            for entry in entries:
                name = _safe_name(entry.filename)
                if entry.is_dir():
                    continue
                if name in files:
                    raise WallImportError("Duplicate path in wall pack.")
                files[name] = entry
            sets = []
            for name in sorted(files):
                if not name.lower().endswith((".json", ".db", ".uvtt", ".dd2vtt", ".df2vtt")):
                    continue
                content = archive.read(files[name])
                if content.startswith(b"PK"):
                    raise WallImportError("Nested archives are not supported.")
                try:
                    parsed = parser(content, name)
                except WallImportError:
                    continue  # Packs may include unrelated JSON metadata.
                for ws in parsed:
                    if ws.image_reference and ":" not in ws.image_reference:
                        ref = _safe_name(ws.image_reference)
                        relative = posixpath.normpath(posixpath.join(posixpath.dirname(name), ref))
                        asset = files.get(ref) or files.get(relative)
                        if asset is not None:
                            ws.image_data = base64.b64encode(archive.read(asset)).decode("ascii")
                            ws.image_is_thumbnail = False
                    sets.append(ws)
            if not sets:
                raise WallImportError("No supported wall sets found in ZIP pack.")
            return sets
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError, OSError) as exc:
        raise WallImportError(f"Cannot read ZIP wall pack: {exc}") from exc

"""Battle map image import / validation."""

import io
import logging
import uuid
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

log = logging.getLogger(__name__)

ALLOWED_FORMATS = {"PNG": "png", "JPEG": "jpg", "WEBP": "webp", "GIF": "gif", "BMP": "bmp", "TIFF": "tif"}


class ImageImportError(ValueError):
    pass


@dataclass(slots=True, frozen=True)
class StoredImage:
    relative_path: str  # relative to maps_dir
    width: int
    height: int


def configure(max_pixels: int) -> None:
    Image.MAX_IMAGE_PIXELS = max_pixels


def store_map_image(raw: bytes, maps_dir: Path, campaign_id: int) -> StoredImage:
    """Validate an uploaded image and store it under maps_dir/<campaign_id>/<uuid>.<ext>."""
    if not raw:
        raise ImageImportError("Empty file")
    try:
        with Image.open(io.BytesIO(raw)) as probe:
            probe.verify()
        with Image.open(io.BytesIO(raw)) as img:
            fmt = img.format
            img.seek(0)
            canonical = ImageOps.exif_transpose(img).convert("RGB")
            w, h = canonical.size
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ImageImportError(f"Not a supported image: {exc}") from exc
    if fmt not in ALLOWED_FORMATS:
        raise ImageImportError(f"Unsupported image format {fmt}; use PNG, JPEG or WEBP")
    rel = Path(str(campaign_id)) / f"{uuid.uuid4().hex}.png"
    dest = maps_dir / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    # Acquire ownership before encoding; a collision must never overwrite/delete a file.
    stream = dest.open("xb")
    try:
        with stream:
            canonical.save(stream, "PNG")
    except BaseException:
        try:
            dest.unlink(missing_ok=True)
        except OSError:
            log.warning("Could not remove failed map image %s", rel, exc_info=True)
        raise
    return StoredImage(rel.as_posix(), w, h)


def delete_map_image(maps_dir: Path, relative_path: str) -> None:
    p = (maps_dir / relative_path).resolve()
    if maps_dir.resolve() in p.parents:
        p.unlink(missing_ok=True)

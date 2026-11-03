#!/usr/bin/env python3
"""Create bounded, lossless reading copies of CI evidence; keep originals."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

LIMIT = 4000
NAME = "reader-chunks"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def pieces(text):
    current = bytearray()
    for char in text:
        encoded = char.encode("utf-8")
        if len(current) + len(encoded) > LIMIT:
            yield bytes(current)
            current.clear()
        current.extend(encoded)
    if current:
        yield bytes(current)


def write_bounded(path, data):
    if len(data) > LIMIT:
        raise ValueError(f"Metadata exceeds {LIMIT} bytes: {path.name}")
    path.write_bytes(data)


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=True, sort_keys=True) + "\n").encode("ascii")


def sources(root):
    result = []
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if relative.parts[0] == NAME:
            continue
        if path.is_symlink():
            raise ValueError(f"Symlinks are not supported: {relative}")
        if path.is_file():
            result.append(path)
    return sorted(result)


def verify(root, reader):
    actual = sources(root)
    expected = []
    directories = sorted(p for p in reader.iterdir() if p.is_dir())
    for directory in directories:
        meta = json.loads((directory / "metadata.json").read_text("ascii"))
        relative = Path(meta["source"])
        if relative.is_absolute() or ".." in relative.parts or relative.parts[0] == NAME:
            raise ValueError("Unsafe source path in metadata")
        source = root / relative
        if source.is_symlink() or not source.is_file():
            raise ValueError(f"Missing or unsafe source: {relative}")
        original = source.read_bytes()
        encoded = bytearray()
        rows = []
        for number in range(1, meta["parts"] + 1):
            part = directory / f"part-{number:06d}.txt"
            data = part.read_bytes()
            if len(data) > LIMIT:
                raise ValueError(f"Oversized part: {part}")
            data.decode("utf-8")
            encoded.extend(data)
            rows.append(f"{part.name} {len(data)} {digest(data)}\n")
        hash_text = "".join(rows).encode("ascii")
        hash_parts = b"".join(p.read_bytes() for p in sorted(directory.glob("hashes-*.txt")))
        if hash_parts != hash_text:
            raise ValueError(f"Part checksum mismatch: {relative}")
        recovered = bytes(encoded)
        if meta["encoding"] == "base64":
            recovered = base64.b64decode(recovered, validate=True)
        elif meta["encoding"] != "utf-8":
            raise ValueError("Unknown encoding")
        if recovered != original or len(original) != meta["bytes"] or digest(original) != meta["sha256"]:
            raise ValueError(f"Reconstruction mismatch: {relative}")
        expected.append(source)
    if sorted(expected) != actual:
        raise ValueError("Source inventory differs from reading copy")
    for path in reader.rglob("*"):
        if path.is_file() and path.stat().st_size > LIMIT:
            raise ValueError(f"Oversized reader file: {path}")
    return len(expected)


def build(root):
    reader = root / NAME
    if reader.exists():
        raise ValueError(f"{reader} already exists; refusing to overwrite")
    original_sources = sources(root)
    staging = Path(tempfile.mkdtemp(prefix="ci-reader-", dir=root.parent))
    try:
        index = []
        for number, source in enumerate(original_sources, 1):
            relative = source.relative_to(root).as_posix()
            data = source.read_bytes()
            try:
                text = data.decode("utf-8")
                if any(ord(c) < 32 and c not in "\n\r\t" for c in text):
                    raise ValueError("Binary control characters")
                encoding = "utf-8"
            except (UnicodeDecodeError, ValueError):
                text = base64.b64encode(data).decode("ascii")
                encoding = "base64"
            directory = staging / f"file-{number:06d}"
            directory.mkdir()
            hashes = []
            count = 0
            for count, part in enumerate(pieces(text), 1):
                name = f"part-{count:06d}.txt"
                write_bounded(directory / name, part)
                hashes.append(f"{name} {len(part)} {digest(part)}\n")
            meta = {"source": relative, "bytes": len(data), "sha256": digest(data), "encoding": encoding, "parts": count, "max_part_bytes": LIMIT}
            write_bounded(directory / "metadata.json", json_bytes(meta))
            for page, part in enumerate(pieces("".join(hashes)), 1):
                write_bounded(directory / f"hashes-{page:06d}.txt", part)
            index.append(json.dumps({"directory": directory.name, "source": relative}, ensure_ascii=True) + "\n")
        for page, part in enumerate(pieces("".join(index)), 1):
            write_bounded(staging / f"index-{page:06d}.jsonl.txt", part)
        instructions = (
            "CI evidence reading copy, format 1\n"
            f"Maximum file size: {LIMIT} bytes. Original evidence is unchanged.\n"
            "Read index-*.jsonl.txt in numeric order. Index pages may split a JSON line; concatenate before parsing.\n"
            "Each file-NNNNNN/metadata.json names the original relative path, encoding, byte count, SHA-256 and part count.\n"
            "Read part-NNNNNN.txt files in numeric order. Concatenate bytes without adding or removing newlines.\n"
            "UTF-8 parts never split a code point; lines/XML elements may span parts. Parts are fragments, not standalone XML.\n"
            "For base64 encoding, concatenate all parts, then base64-decode to recover the original bytes.\n"
            "Empty originals have zero parts and reconstruct to empty bytes.\n"
            "Concatenate hashes-*.txt in numeric order for part filename, byte count and SHA-256 records.\n"
            "Verify reconstructed bytes against metadata.json.\n"
            "Local verification: python3 tools/chunk_ci_evidence.py --verify EVIDENCE_DIRECTORY\n"
            "The connector threshold is unknown; 4000 bytes is a conservative target, not a guaranteed connector contract.\n"
        )
        write_bounded(staging / "README.txt", instructions.encode("utf-8"))
        count = verify(root, staging)
        staging.rename(reader)
        return count
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="verify existing reader chunks against originals")
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    root = args.directory.resolve()
    if not root.is_dir():
        parser.error("Evidence directory does not exist")
    try:
        count = verify(root, root / NAME) if args.verify else build(root)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(1, f"ERROR: {exc}\n")
    print(f"Verified lossless reader chunks for {count} source files in {root / NAME}")


if __name__ == "__main__":
    main()

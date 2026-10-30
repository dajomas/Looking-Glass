"""Regression checks for lossless, bounded CI evidence reading copies."""
import base64
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("ci_chunk_tool", ROOT / "tools/chunk_ci_evidence.py")
chunk = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(chunk)


@pytest.mark.parametrize("payload", [
    ("map \u2192 \U0001f409\r\n" * 2000).encode("utf-8"),
    b"<testsuite>" + b"<testcase/>" * 3000 + b"</testsuite>",
    bytes(range(256)) * 50,
    b"",
], ids=["unicode-crlf", "single-line-xml", "binary", "empty"])
def test_exact_reconstruction_and_file_size_bounds(tmp_path, payload):
    (tmp_path / "evidence").write_bytes(payload)
    assert chunk.build(tmp_path) == 1
    reader = tmp_path / chunk.NAME
    assert chunk.verify(tmp_path, reader) == 1
    directory = reader / "file-000001"
    meta = json.loads((directory / "metadata.json").read_text())
    raw = b"".join(path.read_bytes() for path in sorted(directory.glob("part-*.txt")))
    if meta["encoding"] == "base64":
        raw = base64.b64decode(raw, validate=True)
    assert raw == payload
    assert (tmp_path / "evidence").read_bytes() == payload
    assert all(path.stat().st_size <= chunk.LIMIT for path in reader.rglob("*") if path.is_file())


@pytest.mark.parametrize("damage", ["changed-part", "missing-part", "changed-source"])
def test_verification_rejects_damaged_evidence(tmp_path, damage):
    original = tmp_path / "evidence"
    original.write_bytes(b"original" * 1000)
    chunk.build(tmp_path)
    reader = tmp_path / chunk.NAME
    part = reader / "file-000001/part-000001.txt"
    if damage == "changed-part":
        part.write_bytes(b"changed")
    elif damage == "missing-part":
        part.unlink()
    else:
        original.write_bytes(b"different")
    with pytest.raises((OSError, ValueError)):
        chunk.verify(tmp_path, reader)


def test_existing_reading_copy_is_not_overwritten(tmp_path):
    (tmp_path / "evidence").write_bytes(b"original")
    chunk.build(tmp_path)
    before = {path.relative_to(tmp_path): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    with pytest.raises(ValueError, match="already exists"):
        chunk.build(tmp_path)
    assert before == {path.relative_to(tmp_path): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}


def test_paginated_index_reconstructs_complete_inventory(tmp_path):
    for number in range(60):
        (tmp_path / f"long-evidence-filename-{number:03d}.txt").write_text(str(number))
    assert chunk.build(tmp_path) == 60
    reader = tmp_path / chunk.NAME
    pages = sorted(reader.glob("index-*.jsonl.txt"))
    assert len(pages) > 1
    records = [json.loads(line) for line in b"".join(path.read_bytes() for path in pages).decode().splitlines()]
    assert len(records) == 60
    assert {record["source"] for record in records} == {f"long-evidence-filename-{n:03d}.txt" for n in range(60)}
    assert chunk.verify(tmp_path, reader) == 60

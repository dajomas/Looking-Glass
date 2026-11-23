"""Bug 31: an invalid colour aborts the CLI cleanly before any storage write."""
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("command", ["serve", "list-users"])
@pytest.mark.parametrize("text", ["fog:\n  fog_color: #808080\n", "fog:\n  fog_color: grey\n"])
def test_invalid_colour_aborts_without_traceback_or_writes(tmp_path, command, text):
    path = tmp_path / "bad.yaml"
    path.write_text(text, encoding="utf-8")
    data = tmp_path / "must-not-exist"
    environment = dict(os.environ)
    for name in ("LG_CONFIG", "LG_HOST", "LG_ADMIN_PORT", "LG_VIEWER_PORT", "LG_DATA_DIR"):
        environment.pop(name, None)
    environment["LG_DATA_DIR"] = str(data)
    result = subprocess.run([sys.executable, str(ROOT / "python/main.py"), "--config", str(path), command],
                            cwd=tmp_path, env=environment, capture_output=True, text=True, timeout=20)
    assert result.returncode == 2, result.stderr
    assert result.stderr.startswith("Configuration error: "), result.stderr
    assert str(path) in result.stderr
    assert "'fog.fog_color'" in result.stderr
    assert "Traceback" not in result.stderr
    assert not data.exists(), "No directories, migrations or bootstrap data may be written"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["bad.yaml"]

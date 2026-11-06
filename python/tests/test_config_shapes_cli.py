"""Bug 24: malformed config must fail before CLI storage/bootstrap writes."""
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("selection", ["argument", "environment"])
@pytest.mark.parametrize("text,diagnostic", [
    ("false\n", "configuration must be a mapping"),
    ("[]\n", "configuration must be a mapping"),
    ("server: null\n", "section 'server' must be a mapping"),
    ("storage: false\n", "section 'storage' must be a mapping"),
])
def test_malformed_config_aborts_before_bootstrap(tmp_path, selection, text, diagnostic):
    path = tmp_path / "bad.yaml"
    path.write_text(text, encoding="utf-8")
    data = tmp_path / "must-not-exist"
    environment = dict(os.environ)
    for name in ("LG_CONFIG", "LG_HOST", "LG_ADMIN_PORT", "LG_VIEWER_PORT", "LG_DATA_DIR"):
        environment.pop(name, None)
    environment["LG_DATA_DIR"] = str(data)
    args = [sys.executable, str(ROOT / "python/main.py")]
    if selection == "argument":
        args.extend(["--config", str(path)])
    else:
        environment["LG_CONFIG"] = str(path)
    args.append("list-users")
    result = subprocess.run(args, cwd=tmp_path, env=environment,
                            capture_output=True, text=True, timeout=20)
    assert result.returncode != 0
    assert str(path) in result.stderr, result.stderr
    assert diagnostic in result.stderr, result.stderr
    assert not data.exists(), "No directories, migrations or bootstrap data may be written"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["bad.yaml"]

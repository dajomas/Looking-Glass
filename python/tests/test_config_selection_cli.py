"""CLI no-bootstrap regression for bug 23; needs the normal application runtime."""
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("selection", ["argument", "environment"])
def test_missing_config_aborts_cli_before_database_initialization(tmp_path, selection):
    missing = tmp_path / "missing-config.yaml"
    data = tmp_path / "must-not-exist"
    environment = dict(os.environ, LG_DATA_DIR=str(data))
    environment.pop("LG_CONFIG", None)
    args = [sys.executable, str(ROOT / "python/main.py")]
    if selection == "argument":
        args.extend(["--config", str(missing)])
    else:
        environment["LG_CONFIG"] = str(missing)
    args.append("list-users")
    result = subprocess.run(args, cwd=tmp_path, env=environment,
                            capture_output=True, text=True, timeout=20)
    assert result.returncode != 0
    assert str(missing) in result.stderr, result.stderr
    assert not data.exists(), "No directories, migrations or bootstrap data may be written"

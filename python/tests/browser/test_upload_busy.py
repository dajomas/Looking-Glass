"""Run the standalone async browser check outside the sync Playwright loop."""
from pathlib import Path
import subprocess
import sys


def test_upload_busy_browser_regression():
    root = Path(__file__).resolve().parents[3]
    source = root / "python/tests/check_upload_busy_browser.py"
    result = subprocess.run(
        [sys.executable, str(source)],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, (
        f"Upload-busy browser check exited with {result.returncode}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )

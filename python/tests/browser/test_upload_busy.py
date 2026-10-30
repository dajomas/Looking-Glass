"""Include the existing standalone upload-busy check in browser discovery."""
import asyncio
from pathlib import Path
import runpy


def test_upload_busy_browser_regression():
    source = Path(__file__).resolve().parents[1] / "check_upload_busy_browser.py"
    check = runpy.run_path(str(source))["main"]
    checks = asyncio.run(check())
    assert checks, "Upload-busy regression did not report completed checks"

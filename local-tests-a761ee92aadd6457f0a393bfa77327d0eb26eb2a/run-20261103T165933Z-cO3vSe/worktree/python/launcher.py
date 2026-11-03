"""Shared stdlib-only setup for run.sh, run.bat and run.ps1."""
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parents[1]


def main():
    if sys.version_info < (3, 12):
        raise SystemExit("Looking Glass requires Python 3.12 or newer. Set LG_PYTHON to a suitable executable.")
    os.chdir(ROOT)
    args = sys.argv[1:]
    force = "--install" in args
    offline = "--no-install" in args
    args = [a for a in args if a not in ("--install", "--no-install")]
    if force and offline:
        raise SystemExit("Use either --install or --no-install, not both.")
    env_dir = ROOT / ".venv"
    python = env_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not python.is_file():
        if offline:
            raise SystemExit("No .venv found. Run without --no-install to create it.")
        venv.EnvBuilder(with_pip=True).create(env_dir)
    subprocess.run([str(python), "-c", "import sys; sys.exit(0 if sys.version_info >= (3,12) else 1)"], check=True)
    requirements = ROOT / "requirements.txt"
    digest = hashlib.sha256(requirements.read_bytes()).hexdigest()
    stamp = env_dir / ".looking-glass-requirements.sha256"
    if not offline and (force or not stamp.exists() or stamp.read_text().strip() != digest):
        subprocess.run([str(python), "-m", "pip", "install", "-r", str(requirements)], check=True)
        stamp.write_text(digest + "\n")
    print("Starting Looking Glass (defaults: admin 5000, viewer 5100; configuration/env overrides apply)", flush=True)
    return subprocess.call([str(python), str(ROOT / "python/main.py"), *args])


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"Startup failed: {exc}", file=sys.stderr)
        raise SystemExit(1)

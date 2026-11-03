#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [[ -n "${LG_PYTHON:-}" ]]; then
  python="$LG_PYTHON"
elif [[ -x .venv/bin/python ]]; then
  python=.venv/bin/python
else
  python=""
  for candidate in python3.14 python3.13 python3.12 python3 python; do
    if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; sys.exit(sys.version_info < (3,12))'; then
      python="$candidate"; break
    fi
  done
  if [[ -z "$python" ]]; then echo "Python 3.12+ is required. Set LG_PYTHON." >&2; exit 1; fi
fi
exec "$python" python/launcher.py "$@"

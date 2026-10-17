#!/usr/bin/env python3.14
"""Looking Glass entry point:  python3.14 python/main.py [serve|create-user|reset-password|list-users]"""

import sys
from pathlib import Path

if sys.version_info < (3, 14):
    sys.exit("Looking Glass requires Python 3.14 or newer")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from looking_glass.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())

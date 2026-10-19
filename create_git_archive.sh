NAME=looking-glass
BRANCH=$(git rev-parse --abbrev-ref HEAD)
git rev-parse ${BRANCH}
HASH=$(git rev-parse ${BRANCH} | cut -c1-7)

echo "Create git archive for branch ${BRANCH} (${HASH})"
git archive --format=zip --output=${NAME}-source.zip ${BRANCH}

echo "Convert zip file to base64"
python3 - ${HASH} ${NAME}<<'PY'
import base64, sys, os
from pathlib import Path

HASH=sys.argv[1]
NAME=sys.argv[2]
source = Path(f"{NAME}-source.zip")
target = Path(f"{NAME}-source-{HASH}-base64.txt")
target.write_text(
    base64.b64encode(source.read_bytes()).decode("ascii"),
    encoding="ascii",
)
os.unlink(source)
PY

BRANCH=$(git rev-parse --abbrev-ref HEAD)
HASH=$(git rev-parse --short=7 HEAD 2>/dev/null) || HASH=unversioned

echo "Create git archive for branch ${BRANCH} (${HASH})"
git archive --format=zip  ${BRANCH} | base64 > looking-glass-source-${HASH}-base64.txt

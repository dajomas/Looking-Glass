#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

REPO="dajomas/Looking-Glass"
BRANCH="features/perplexity"
WORKFLOW="integration-tests.yml"
RUN_ID=""
PUBLISH=0
TMP=""

die() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 1
}

usage() {
    cat <<'EOF'
Usage: bash getworkflow.sh [RUN_ID] [--publish]

Without RUN_ID, collect the latest completed integration workflow run.
Without --publish, collect locally without committing or pushing.
With --publish, require a clean, up-to-date features/perplexity checkout,
then prompt before committing and pushing only the collected evidence.
Requires Bash, Git, authenticated GitHub CLI, jq and Python 3.
Creates lossless reader-chunks alongside the unchanged original evidence.
To chunk existing evidence without downloading again:
  python3 tools/chunk_ci_evidence.py ci-results-RUN_ID-attempt-ATTEMPT
To verify the reading copy against the originals:
  python3 tools/chunk_ci_evidence.py --verify ci-results-RUN_ID-attempt-ATTEMPT
EOF
}

trap '[[ -z "$TMP" ]] || rm -rf -- "$TMP"' EXIT

for arg in "$@"; do
    case "$arg" in
        --publish) PUBLISH=1 ;;
        -h|--help) usage; exit 0 ;;
        *)
            [[ "$arg" =~ ^[0-9]+$ ]] || die "Unknown argument: $arg"
            [[ -z "$RUN_ID" ]] || die "Specify only one run ID."
            RUN_ID="$arg"
            ;;
    esac
done

for command in gh jq git mktemp python3; do
    command -v "$command" >/dev/null || die "Required command not found: $command"
done

gh auth status >/dev/null 2>&1 || die "Authenticate first: gh auth login"
ROOT="$(git rev-parse --show-toplevel)" || die "Run inside the Looking-Glass checkout."
cd "$ROOT"
[[ -f tools/chunk_ci_evidence.py ]] || die "Missing tools/chunk_ci_evidence.py"
ACTUAL_REPO="$(gh repo view --json nameWithOwner --jq '.nameWithOwner')"
[[ "${ACTUAL_REPO,,}" == "${REPO,,}" ]] || die "Checkout resolves to $ACTUAL_REPO, expected $REPO."

if (( PUBLISH )); then
    [[ "$(git branch --show-current)" == "$BRANCH" ]] || die "Publishing requires branch $BRANCH."
    [[ -z "$(git status --porcelain)" ]] || die "Publishing requires a clean working tree and index."
    ORIGIN_URL="$(git remote get-url --push origin)"
    case "$ORIGIN_URL" in
        "https://github.com/$REPO"|"https://github.com/$REPO.git"|"git@github.com:$REPO"|"git@github.com:$REPO.git"|"ssh://git@github.com/$REPO"|"ssh://git@github.com/$REPO.git") ;;
        *) die "Unexpected origin push URL: $ORIGIN_URL" ;;
    esac
    git fetch origin "refs/heads/$BRANCH"
    [[ "$(git rev-parse HEAD)" == "$(git rev-parse FETCH_HEAD)" ]] || die "Local HEAD differs from origin/$BRANCH; reconcile first."
fi

if [[ -z "$RUN_ID" ]]; then
    RUN_ID="$(gh run list --repo "$REPO" --workflow "$WORKFLOW" --branch "$BRANCH" --status completed --limit 1 --json databaseId --jq '.[0].databaseId // empty')"
    [[ -n "$RUN_ID" ]] || die "No completed workflow run found."
fi

TMP="$(mktemp -d)"
gh run view "$RUN_ID" --repo "$REPO" --json databaseId,workflowDatabaseId,workflowName,headBranch,headSha,status,conclusion,url,attempt,event,createdAt,startedAt,updatedAt,jobs > "$TMP/run.json"
STATUS="$(jq -r '.status' "$TMP/run.json")"
RUN_BRANCH="$(jq -r '.headBranch' "$TMP/run.json")"
RUN_SHA="$(jq -r '.headSha' "$TMP/run.json")"
ATTEMPT="$(jq -r '.attempt' "$TMP/run.json")"
CONCLUSION="$(jq -r '.conclusion' "$TMP/run.json")"
[[ "$STATUS" == "completed" ]] || die "Run $RUN_ID is $STATUS, not completed."
[[ "$RUN_BRANCH" == "$BRANCH" ]] || die "Run belongs to $RUN_BRANCH, expected $BRANCH."
EXPECTED_WORKFLOW_ID="$(gh api "repos/$REPO/actions/workflows/$WORKFLOW" --jq '.id')"
[[ "$(jq -r '.workflowDatabaseId' "$TMP/run.json")" == "$EXPECTED_WORKFLOW_ID" ]] || die "Run does not belong to $WORKFLOW."

OUT="ci-results-${RUN_ID}-attempt-${ATTEMPT}"
[[ ! -e "$OUT" ]] || die "$OUT already exists; refusing to mix or overwrite evidence."
mkdir -p "$OUT/artifacts"
cp "$TMP/run.json" "$OUT/run.json"
{
    printf 'Collected at: %s\n' "$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
    printf 'Repository: %s\nRun ID: %s\nAttempt: %s\n' "$REPO" "$RUN_ID" "$ATTEMPT"
    printf 'Tested SHA: %s\nConclusion: %s\n' "$RUN_SHA" "$CONCLUSION"
    printf 'Collector checkout SHA: %s\n' "$(git rev-parse HEAD)"
    printf 'Artifacts are run-scoped, not guaranteed attempt-specific. Verify contained SHAs and provenance.\n'
} > "$OUT/collection.txt"

if gh run view "$RUN_ID" --repo "$REPO" --attempt "$ATTEMPT" --log > "$OUT/workflow.log" 2> "$OUT/log-download.stderr"; then
    printf 'Full logs: downloaded\n' >> "$OUT/collection.txt"
else
    printf 'WARNING: Full logs unavailable or incomplete; inspect log-download.stderr\n' >> "$OUT/collection.txt"
fi

if gh run download "$RUN_ID" --repo "$REPO" --dir "$OUT/artifacts" > "$OUT/artifact-download.stdout" 2> "$OUT/artifact-download.stderr"; then
    printf 'Artifact download command: succeeded\n' >> "$OUT/collection.txt"
else
    printf 'WARNING: Artifact download failed; artifacts may be missing or partial\n' >> "$OUT/collection.txt"
fi
find "$OUT/artifacts" -type f -print | LC_ALL=C sort > "$OUT/artifact-files.txt"
if [[ ! -s "$OUT/artifact-files.txt" ]]; then
    printf 'WARNING: No artifact files were collected.\n' >> "$OUT/collection.txt"
fi

python3 tools/chunk_ci_evidence.py "$OUT"

printf '\nCollected evidence in %s\n' "$OUT"
cat "$OUT/collection.txt"
printf 'Review the collection report and evidence before publishing.\n'
if (( ! PUBLISH )); then
    printf 'No commit or push performed.\n'
    exit 0
fi

printf '\nLogs/artifacts may contain sensitive data.\n'
printf 'Type "publish" to commit and push this evidence: '
read -r ANSWER
[[ "$ANSWER" == "publish" ]] || die "Publishing cancelled; evidence remains locally."
[[ "$(git branch --show-current)" == "$BRANCH" ]] || die "Branch changed during collection."
git diff --quiet && git diff --cached --quiet || die "Tracked files or index changed during collection; review manually."
python3 tools/chunk_ci_evidence.py --verify "$OUT"
git add -- "$OUT"
git commit -m "Add CI evidence for run ${RUN_ID}, attempt ${ATTEMPT} [skip ci]"
git push origin "HEAD:refs/heads/$BRANCH"
printf '\nPublished commit: %s\n' "$(git rev-parse HEAD)"
printf 'Branch: %s\nEvidence: %s\n' "$BRANCH" "$OUT"

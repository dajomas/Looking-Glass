#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

REPO="dajomas/Looking-Glass"
BRANCH="features/perplexity"
WORKFLOW="integration-tests.yml"
RUN_ID=""
PUBLISH=0
TMP=""
OLD_COLLECTIONS=()

die() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 1
}

usage() {
    cat <<'EOF'
Usage: bash getworkflow.sh [RUN_ID] [--publish]

Require a clean features/perplexity checkout, even for local-only collection.
Without RUN_ID, select the latest completed integration workflow run.
Before downloading, list prior root ci-results-RUN[-attempt-N] directories
and prompt before removing them locally. Dirty/ignored data is not removed.
Without --publish, no commit or push occurs; old deletions remain unstaged.
With --publish, require an up-to-date checkout and prompt before committing
old tracked deletions together with the new evidence and pushing.
Failure after cleanup leaves tracked old evidence recoverable from starting HEAD.
Git history and GitHub Actions artifacts are not deleted.
Requires Bash, Git, authenticated GitHub CLI, jq and Python 3.
Creates lossless reader-chunks alongside the unchanged new original evidence.
To chunk existing evidence without running cleanup or downloading again:
  python3 tools/chunk_ci_evidence.py ci-results-RUN_ID-attempt-ATTEMPT
To verify a reading copy:
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
[[ "$(git branch --show-current)" == "$BRANCH" ]] || die "Collection cleanup requires branch $BRANCH."
[[ -z "$(git status --porcelain)" ]] || die "Cleanup requires a clean working tree and index; preserve or commit local work first."
START_SHA="$(git rev-parse HEAD)"

if (( PUBLISH )); then
    ORIGIN_URL="$(git remote get-url --push origin)"
    case "$ORIGIN_URL" in
        "https://github.com/$REPO"|"https://github.com/$REPO.git"|"git@github.com:$REPO"|"git@github.com:$REPO.git"|"ssh://git@github.com/$REPO"|"ssh://git@github.com/$REPO.git") ;;
        *) die "Unexpected origin push URL: $ORIGIN_URL" ;;
    esac
    git fetch origin "refs/heads/$BRANCH"
    [[ "$START_SHA" == "$(git rev-parse FETCH_HEAD)" ]] || die "Local HEAD differs from origin/$BRANCH; reconcile first."
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
[[ "$ATTEMPT" =~ ^[0-9]+$ ]] || die "Invalid run attempt."
EXPECTED_WORKFLOW_ID="$(gh api "repos/$REPO/actions/workflows/$WORKFLOW" --jq '.id')"
[[ "$(jq -r '.workflowDatabaseId' "$TMP/run.json")" == "$EXPECTED_WORKFLOW_ID" ]] || die "Run does not belong to $WORKFLOW."

OUT="ci-results-${RUN_ID}-attempt-${ATTEMPT}"
[[ ! -e "$OUT" && ! -L "$OUT" ]] || die "$OUT already exists; select a new run/attempt or use the chunk helper for existing evidence."
for candidate in ci-results-*; do
    [[ "$candidate" =~ ^ci-results-[0-9]+(-attempt-[0-9]+)?$ ]] || continue
    [[ ! -L "$candidate" && -d "$candidate" ]] || die "Refusing non-directory or symlink collection: $candidate"
    [[ -z "$(git ls-files --others --ignored --exclude-standard -- "$candidate")" ]] || die "Ignored local files exist inside $candidate; preserve them before cleanup."
    OLD_COLLECTIONS+=("$candidate")
done

if (( ${#OLD_COLLECTIONS[@]} )); then
    printf '\nPrior collections to remove locally before downloading:\n'
    printf '  %s\n' "${OLD_COLLECTIONS[@]}"
    printf 'Starting commit for tracked-file recovery: %s\n' "$START_SHA"
    printf 'With --publish, tracked deletions will be committed with the new evidence.\n'
    printf 'Type "remove" to remove these directories and continue: '
    read -r CLEANUP_ANSWER
    [[ "$CLEANUP_ANSWER" == "remove" ]] || die "Cleanup cancelled; no collection directories removed."
    [[ "$(git branch --show-current)" == "$BRANCH" && "$(git rev-parse HEAD)" == "$START_SHA" ]] || die "Checkout changed before cleanup."
    [[ -z "$(git status --porcelain)" ]] || die "Working tree changed before cleanup."
    for candidate in "${OLD_COLLECTIONS[@]}"; do
        [[ ! -L "$candidate" && -d "$candidate" ]] || die "Collection changed before cleanup: $candidate"
        [[ -z "$(git ls-files --others --ignored --exclude-standard -- "$candidate")" ]] || die "Ignored files appeared in $candidate; cleanup stopped."
    done
    for candidate in "${OLD_COLLECTIONS[@]}"; do
        rm -rf -- "$candidate"
    done
    printf 'Old tracked files remain recoverable from %s if collection fails.\n' "$START_SHA"
fi

mkdir -p "$OUT/artifacts"
cp "$TMP/run.json" "$OUT/run.json"
{
    printf 'Collected at: %s\n' "$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
    printf 'Repository: %s\nRun ID: %s\nAttempt: %s\n' "$REPO" "$RUN_ID" "$ATTEMPT"
    printf 'Tested SHA: %s\nConclusion: %s\n' "$RUN_SHA" "$CONCLUSION"
    printf 'Collector checkout SHA: %s\n' "$START_SHA"
    printf 'Artifacts are run-scoped, not guaranteed attempt-specific. Verify contained SHAs and provenance.\n'
    for candidate in "${OLD_COLLECTIONS[@]}"; do
        printf 'Prior collection removed locally: %s\n' "$candidate"
    done
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
    printf 'No commit or push performed. Prior tracked deletions remain unstaged; GitHub is unchanged.\n'
    exit 0
fi

printf '\nLogs/artifacts may contain sensitive data.\n'
printf 'Publication includes the new evidence and these prior collection deletions:\n'
if (( ${#OLD_COLLECTIONS[@]} )); then
    printf '  %s\n' "${OLD_COLLECTIONS[@]}"
else
    printf '  (none)\n'
fi
printf 'Type "publish" to commit and push: '
read -r ANSWER
[[ "$ANSWER" == "publish" ]] || die "Publishing cancelled; evidence and local deletions remain for review."
[[ "$(git branch --show-current)" == "$BRANCH" && "$(git rev-parse HEAD)" == "$START_SHA" ]] || die "Checkout changed during collection."
git diff --cached --quiet || die "Index changed during collection; review manually."
python3 - "${OLD_COLLECTIONS[@]}" <<'PY'
import os
import subprocess
import sys
allowed = set(sys.argv[1:])
fields = subprocess.check_output(["git", "diff", "--name-status", "--no-renames", "-z"]).split(b"\0")
for index in range(0, len(fields) - 1, 2):
    status = fields[index]
    path = os.fsdecode(fields[index + 1])
    if status != b"D" or path.split("/", 1)[0] not in allowed:
        raise SystemExit(f"Unexpected tracked change during collection: {status!r} {path}")
PY
python3 tools/chunk_ci_evidence.py --verify "$OUT"
git add -A -- "$OUT" "${OLD_COLLECTIONS[@]}"
git commit -m "Replace CI evidence with run ${RUN_ID}, attempt ${ATTEMPT} [skip ci]"
git push origin "HEAD:refs/heads/$BRANCH"
printf '\nPublished commit: %s\n' "$(git rev-parse HEAD)"
printf 'Branch: %s\nEvidence: %s\n' "$BRANCH" "$OUT"
CURRENT_SHA="$(git rev-parse HEAD)"
printf '\nCopy/paste the following message:\n\n'
printf 'The new databaseId is %s and is against commit hash %s\n\n' "$RUN_ID" "$RUN_SHA"
printf 'Current commit hash is %s\n' "$CURRENT_SHA"

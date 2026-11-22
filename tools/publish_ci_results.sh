#!/usr/bin/env bash
# Run only from the trusted default-branch collector checkout.
set -Eeuo pipefail
umask 077
: "${GH_TOKEN:?}" "${GH_REPO:?}" "${RUN_ID:?}" "${RUN_ATTEMPT:?}" "${BRANCH:?}" "${EXPECTED_SHA:?}" "${RUNNER_TEMP:?}"
[[ "$RUN_ID" =~ ^[0-9]+$ && "$RUN_ATTEMPT" =~ ^[0-9]+$ ]]
case "$BRANCH" in features/perplexity|features/perplexity-statblock|features/claude|features/claude-statblock) ;; *) exit 1 ;; esac
PUBLICATION="$(cd "${1:?publication checkout required}" && pwd)"
WORK="$RUNNER_TEMP/ci-publication"
mkdir -p "$WORK"
OUT="$WORK/ci-results-${RUN_ID}-attempt-${RUN_ATTEMPT}"
mkdir "$OUT"
mkdir "$OUT/artifacts"
# Query the exact attempt, never the latest run or latest attempt.
gh api "repos/$GH_REPO/actions/runs/$RUN_ID/attempts/$RUN_ATTEMPT" > "$WORK/api-run.json"
jq -e --arg branch "$BRANCH" --arg sha "$EXPECTED_SHA" --argjson attempt "$RUN_ATTEMPT" '
  .status == "completed" and .head_branch == $branch and .head_sha == $sha
  and .run_attempt == $attempt and .event == "push"
  and .path == ".github/workflows/tests.yml"
' "$WORK/api-run.json" >/dev/null
jq '{databaseId: .id, workflowDatabaseId: .workflow_id, workflowName: .name,
  headBranch: .head_branch, headSha: .head_sha, status, conclusion,
  url: .html_url, attempt: .run_attempt, event, createdAt: .created_at,
  startedAt: .run_started_at, updatedAt: .updated_at}' "$WORK/api-run.json" > "$OUT/run.json"
gh api --paginate "repos/$GH_REPO/actions/runs/$RUN_ID/attempts/$RUN_ATTEMPT/jobs?per_page=100" --jq '.jobs[]' | jq -s . > "$OUT/jobs.json"
{
  printf 'Collected at: %s\n' "$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
  printf 'Repository: %s\nRun ID: %s\nAttempt: %s\nBranch: %s\nTested SHA: %s\n' "$GH_REPO" "$RUN_ID" "$RUN_ATTEMPT" "$BRANCH" "$EXPECTED_SHA"
  jq -r '"Conclusion: " + .conclusion' "$OUT/run.json"
  printf 'Artifacts are run-scoped, not guaranteed attempt-specific. Verify their provenance.\n'
  printf 'Publication is automatic; no manual sensitive-data review occurs.\n'
} > "$OUT/collection.txt"
if gh run view "$RUN_ID" --attempt "$RUN_ATTEMPT" --log > "$OUT/workflow.log" 2> "$OUT/log-download.stderr"; then
  echo 'Full logs: downloaded' >> "$OUT/collection.txt"
else
  echo 'WARNING: Logs unavailable or incomplete; inspect log-download.stderr.' >> "$OUT/collection.txt"
fi
if gh run download "$RUN_ID" --dir "$OUT/artifacts" > "$OUT/artifact-download.stdout" 2> "$OUT/artifact-download.stderr"; then
  echo 'Artifact download: succeeded' >> "$OUT/collection.txt"
else
  echo 'WARNING: Artifacts unavailable or partial; inspect artifact-download.stderr.' >> "$OUT/collection.txt"
fi
(cd "$OUT" && find artifacts -type f -print | LC_ALL=C sort) > "$OUT/artifact-files.txt"
[[ -s "$OUT/artifact-files.txt" ]] || echo 'WARNING: No artifact files collected.' >> "$OUT/collection.txt"
# Downloaded evidence is never executed. Reject links before copying.
[[ -z "$(find "$OUT" -type l -print -quit)" ]]
cd "$PUBLICATION"
git config user.name 'github-actions[bot]'
git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
NEW_TIME="$(jq -r .createdAt "$OUT/run.json")"
NAME="$(basename "$OUT")"
for retry in 1 2 3; do
  git fetch origin "refs/heads/$BRANCH"
  # Dedicated disposable checkout; preserve all concurrent remote changes.
  git reset --hard FETCH_HEAD
  OLD=()
  while IFS= read -r path; do
    [[ "$path" =~ ^ci-results-[0-9]+(-attempt-[0-9]+)?$ ]] || continue
    if [[ -f "$path/run.json" ]]; then
      OLD_TIME="$(jq -r '.createdAt // empty' "$path/run.json")"
      OLD_ID="$(jq -r '.databaseId // empty' "$path/run.json")"
      OLD_ATTEMPT="$(jq -r '.attempt // 0' "$path/run.json")"
      if [[ "$OLD_TIME" > "$NEW_TIME" ]] || { [[ "$OLD_ID" == "$RUN_ID" && "$OLD_ATTEMPT" =~ ^[0-9]+$ ]] && (( OLD_ATTEMPT > RUN_ATTEMPT )); }; then
        echo 'Newer evidence already published; leaving it unchanged.' >> "$GITHUB_STEP_SUMMARY"
        exit 0
      fi
    fi
    OLD+=("$path")
  done < <(git ls-tree -d --name-only HEAD)
  for path in "${OLD[@]}"; do git rm -r -- "$path"; done
  [[ ! -e "$NAME" && ! -L "$NAME" ]]
  cp -R -- "$OUT" "$NAME"
  git add -f -- "$NAME"
  if git diff --cached --quiet; then
    echo 'Identical evidence already published.' >> "$GITHUB_STEP_SUMMARY"
    exit 0
  fi
  git commit -m "ci: publish run $RUN_ID attempt $RUN_ATTEMPT [skip ci]"
  if git push origin "HEAD:refs/heads/$BRANCH"; then
    {
      printf 'Published evidence: `%s`\n\nBranch: `%s`\n\n' "$NAME" "$BRANCH"
      printf 'Tested SHA: `%s`\n\nPublication SHA: `%s`\n' "$EXPECTED_SHA" "$(git rev-parse HEAD)"
    } >> "$GITHUB_STEP_SUMMARY"
    exit 0
  fi
  sleep "$retry"
done
echo 'Publication failed after three non-force attempts.' >&2
exit 1

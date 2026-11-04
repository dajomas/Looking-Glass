#!/usr/bin/env bash
# Test committed sources; publish completed evidence from the original checkout.
set -Eeuo pipefail
usage() {
  cat <<'HELP'
Usage: bash runlocaltests.sh [--suite all|python|javascript|browser|live|recovery] [--python PATH] [--no-publish]
Default: all five groups, then publish completed evidence on features/perplexity.
--no-publish keeps evidence local and does not stage, commit or push anything.
Needs installed dependencies and Podman or Docker for recovery.
Tests full committed HEAD; short hashes label local-tests-<short-hash>/ only.
LG_LOCAL_TEST_TMPDIR overrides the native scratch default /tmp.
HELP
}
suite=all
python_arg=""
publish=1
completed=0
while (($#)); do
  case "$1" in
    --help|-h) usage; exit 0 ;;
    --no-publish) publish=0; shift ;;
    --suite|--python)
      (($# >= 2)) || { usage >&2; exit 2; }
      if [[ "$1" == --suite ]]; then suite=$2; else python_arg=$2; fi
      shift 2 ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
done
case "$suite" in all|python|javascript|browser|live|recovery) ;; *) usage >&2; exit 2 ;; esac
ROOT=$(git -C "$(dirname -- "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)
HASH=$(git -C "$ROOT" rev-parse --verify 'HEAD^{commit}')
SHORT_HASH=$(git -C "$ROOT" rev-parse --short=7 "$HASH")
if [[ -n "$python_arg" ]]; then
  PY=$(command -v -- "$python_arg")
elif [[ -n "${VIRTUAL_ENV:-}" && -x "$VIRTUAL_ENV/bin/python" ]]; then
  PY=$VIRTUAL_ENV/bin/python
elif [[ -x "$ROOT/.venv-test/bin/python" ]]; then
  PY=$ROOT/.venv-test/bin/python
elif [[ -x "$ROOT/.venv/bin/python" ]]; then
  PY=$ROOT/.venv/bin/python
else
  PY=$(command -v python3.14 || command -v python3)
fi
[[ "$PY" == /* ]] || PY="$(cd -- "$(dirname -- "$PY")" && pwd)/$(basename -- "$PY")"
BASEDIR=local-tests-$SHORT_HASH
OUT=$ROOT/$BASEDIR
mkdir -p -- "$OUT"
RUN=$(mktemp -d "$OUT/run-$(date -u +%Y%m%dT%H%M%SZ)-XXXXXX")
printf 'Evidence directory: %s\n' "$RUN"
HELPER=$ROOT/tools/local_test_workspace.py
publish_results() {
  local relative=${RUN#"$ROOT/"} branch head
  branch=$(git -C "$ROOT" symbolic-ref --quiet --short HEAD) || return 1
  [[ "$branch" == features/perplexity ]] || { echo 'Refusing publication outside features/perplexity'; return 1; }
  head=$(git -C "$ROOT" rev-parse --verify HEAD) || return 1
  [[ "$head" == "$HASH" ]] || { echo 'HEAD changed during tests; refusing publication'; return 1; }
  git -C "$ROOT" diff --cached --quiet || { echo 'Index has staged changes; refusing publication'; return 1; }
  git -C "$ROOT" add -f -- "$relative" || return 1
  git -C "$ROOT" commit --only -m "Local test results for commit hash $HASH [skip ci]" -- "$relative" || return 1
  git -C "$ROOT" push origin HEAD:refs/heads/features/perplexity || return 1
}
finish() {
  local rc=$? collected=1 publication_log
  trap - EXIT
  if ! cd -- "$ROOT"; then exit 1; fi
  if ! "$PY" "$HELPER" finalize "$RUN" > "$RUN/workspace-finalize.log" 2>&1; then
    rc=1
    collected=0
    printf 'Diagnostic collection failed; inspect workspace-finalize.log. Scratch was retained.\n' >&2
  fi
  printf 'finished_utc=%s\n' "$(date -u +%FT%TZ)" >> "$RUN/environment.txt"
  # This is the test/collection result; publication has separate status outside the committed run.
  printf '%s\n' "$rc" > "$RUN/exit-code.txt"
  if ((publish && completed && collected)); then
    publication_log=$OUT/publication-$(basename -- "$RUN").log
    if publish_results > "$publication_log" 2>&1; then
      printf 'publication_exit=0\n' >> "$publication_log"
      printf 'Published completed local evidence for %s in %s at commit %s\n' \
        "$HASH" "${RUN#"$ROOT/"}" "$(git -C "$ROOT" rev-parse HEAD)"
    else
      rc=1
      printf 'publication_exit=1\n' >> "$publication_log"
      printf 'Evidence publication failed; inspect %s. Local evidence is retained.\n' "$publication_log" >&2
    fi
  elif ((publish)); then
    printf 'Evidence was not published because setup or collection did not complete.\n' >&2
  fi
  exit "$rc"
}
trap finish EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
mkdir -p -- "$RUN/suites"
{
  printf 'commit=%s\nshort_commit=%s\nsuite=%s\npython=%s\nstarted_utc=%s\n' \
    "$HASH" "$SHORT_HASH" "$suite" "$PY" "$(date -u +%FT%TZ)"
  printf 'source=detached sparse clone; uncommitted changes are not tested\n'
  git -C "$ROOT" status --short
  uname -a
} > "$RUN/environment.txt"
"$PY" --version >> "$RUN/environment.txt" 2>&1
if command -v node >/dev/null; then node --version >> "$RUN/environment.txt" 2>&1; fi
WORK=$("$PY" "$HELPER" prepare "$ROOT" "$HASH" "$RUN" 2> "$RUN/workspace-prepare.stderr")
TMPBASE=$(dirname -- "$WORK")/tmp
export PYTHONPATH="$WORK/python"
export PYTHONUNBUFFERED=1
export LG_RUN_LIVE_E2E=1
export LG_RUN_CONTAINER_TESTS=1
cd -- "$WORK"
printf 'suite\ttest_exit\treport_exit\n' > "$RUN/summary.tsv"
capture() {
  local logfile=$1
  shift
  local -a codes
  set +e
  "$@" 2>&1 | tee "$logfile"
  codes=("${PIPESTATUS[@]}")
  set -e
  if ((codes[1] != 0)); then return "${codes[1]}"; fi
  return "${codes[0]}"
}
run_suite() {
  local name=$1 dir=$RUN/suites/$1 test_rc=0 report_rc=0
  mkdir -p -- "$dir"
  printf '\n=== %s ===\n' "$name"
  case "$name" in
    python)
      capture "$dir/pytest.log" "$PY" -m pytest -v -ra --tb=short python/tests \
        --ignore=python/tests/browser --ignore=python/tests/live_e2e --ignore=python/tests/recovery \
        --basetemp="$TMPBASE/python" --junitxml="$dir/results.xml" || test_rc=$? ;;
    javascript)
      capture "$dir/javascript.log" "$PY" tools/run_javascript_tests.py --output-dir "$dir" || test_rc=$? ;;
    browser|live)
      if capture "$dir/browser-preflight.log" "$PY" -u python/tests/check_browser_environment.py; then
        local tests=python/tests/browser
        [[ "$name" != live ]] || tests=python/tests/live_e2e
        capture "$dir/pytest.log" "$PY" -m pytest -v -ra --tb=short "$tests" \
          --basetemp="$TMPBASE/$name" --junitxml="$dir/results.xml" || test_rc=$?
      else
        test_rc=$?
        printf 'NOT RUN: browser preflight failed.\n' > "$dir/pytest.log"
      fi ;;
    recovery)
      capture "$dir/pytest.log" "$PY" -m pytest -v -ra --tb=short python/tests/recovery \
        --basetemp="$TMPBASE/recovery" --junitxml="$dir/results.xml" || test_rc=$? ;;
  esac
  if "$PY" - "$dir/results.xml" > "$dir/report-validation.log" 2>&1 <<'PY'
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
path = Path(sys.argv[1])
if not path.is_file():
    raise SystemExit("FAIL: no JUnit report")
cases = list(ET.parse(path).getroot().iter("testcase"))
failed = [c for c in cases if c.find("failure") is not None or c.find("error") is not None]
skipped = [c for c in cases if c.find("skipped") is not None]
print(f"Reported: {len(cases)}; failed/error: {len(failed)}; skipped: {len(skipped)}")
with path.with_name("failures.txt").open("w", encoding="utf-8") as stream:
    for case in failed + skipped:
        stream.write(f"{case.get('classname', '')}::{case.get('name', '')}\n")
        for child in case:
            if child.tag in ("failure", "error", "skipped"):
                stream.write((child.get("message", "") + "\n" + (child.text or ""))[:2000] + "\n")
if not cases or failed or skipped:
    raise SystemExit("FAIL: required tests must pass without skips")
PY
  then report_rc=0; else report_rc=$?; fi
  printf '%s\t%s\t%s\n' "$name" "$test_rc" "$report_rc" >> "$RUN/summary.tsv"
  printf '%s\n' "$test_rc" > "$dir/test-exit-code.txt"
  printf '%s\n' "$report_rc" > "$dir/report-exit-code.txt"
  ((test_rc == 0 && report_rc == 0))
}
status=0
if [[ "$suite" == all ]]; then suites=(python javascript browser live recovery); else suites=("$suite"); fi
for group in "${suites[@]}"; do
  if run_suite "$group"; then :; else status=1; fi
done
completed=1
printf '\nResults: %s\n' "$RUN"
cat "$RUN/summary.tsv"
exit "$status"

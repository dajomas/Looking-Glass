#!/usr/bin/env bash
# Test committed sources without overwriting checkout data or prior evidence.
set -Eeuo pipefail
usage() {
  cat <<'HELP'
Usage: bash runlocaltests.sh [--suite all|python|javascript|browser|live|recovery] [--python PATH]
Default: all five CI groups, including live browsers and container recovery.
Requires an existing Python test environment, Node.js, Chromium and Docker.
Tests an archived HEAD, not uncommitted edits. No dependencies are installed.
Evidence: local-tests-<full HEAD hash>/run-<UTC timestamp>-<unique suffix>/
HELP
}
suite=all
python_arg=""
while (($#)); do
  case "$1" in
    --help|-h) usage; exit 0 ;;
    --suite|--python)
      (($# >= 2)) || { usage >&2; exit 2; }
      if [[ "$1" == --suite ]]; then suite=$2; else python_arg=$2; fi
      shift 2 ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
done
case "$suite" in all|python|javascript|browser|live|recovery) ;; *) usage >&2; exit 2 ;; esac
ROOT=$(git -C "$(dirname -- "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)
HASH=$(git -C "$ROOT" rev-parse --verify HEAD)
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
# Resolve before changing directories; keep virtual-environment symlinks intact.
[[ "$PY" == /* ]] || PY="$(cd -- "$(dirname -- "$PY")" && pwd)/$(basename -- "$PY")"
OUT=$ROOT/local-tests-$HASH
mkdir -p -- "$OUT"
RUN=$(mktemp -d "$OUT/run-$(date -u +%Y%m%dT%H%M%SZ)-XXXXXX")
printf 'Evidence directory: %s\n' "$RUN"
trap 'rc=$?; printf "%s\n" "$rc" > "$RUN/exit-code.txt"' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
WORK=$RUN/worktree
mkdir -p -- "$WORK" "$RUN/suites" "$RUN/tmp"
{
  printf 'commit=%s\nsuite=%s\npython=%s\nstarted_utc=%s\n' "$HASH" "$suite" "$PY" "$(date -u +%FT%TZ)"
  printf 'source=git archive; uncommitted changes are not tested\n'
  git -C "$ROOT" status --short
  uname -a
} > "$RUN/environment.txt"
"$PY" --version >> "$RUN/environment.txt" 2>&1
if command -v node >/dev/null; then node --version >> "$RUN/environment.txt" 2>&1; fi
# Extract only tracked committed files; do not copy config.yaml, data or environments.
git -C "$ROOT" archive "$HASH" | tar -x -C "$WORK"
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
      capture "$dir/pytest.log" "$PY" -m pytest -v -ra python/tests \
        --ignore=python/tests/browser --ignore=python/tests/live_e2e --ignore=python/tests/recovery \
        --basetemp="$RUN/tmp/python" --junitxml="$dir/results.xml" || test_rc=$? ;;
    javascript)
      capture "$dir/javascript.log" "$PY" tools/run_javascript_tests.py --output-dir "$dir" || test_rc=$? ;;
    browser|live)
      if capture "$dir/browser-preflight.log" "$PY" -u python/tests/check_browser_environment.py; then
        local tests=python/tests/browser
        [[ "$name" != live ]] || tests=python/tests/live_e2e
        capture "$dir/pytest.log" "$PY" -m pytest -v -ra "$tests" \
          --basetemp="$RUN/tmp/$name" --junitxml="$dir/results.xml" || test_rc=$?
      else
        test_rc=$?
        printf 'NOT RUN: browser preflight failed.\n' > "$dir/pytest.log"
      fi ;;
    recovery)
      capture "$dir/pytest.log" "$PY" -m pytest -v -ra python/tests/recovery \
        --basetemp="$RUN/tmp/recovery" --junitxml="$dir/results.xml" || test_rc=$? ;;
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
if [[ "$suite" == all ]]; then
  suites=(python javascript browser live recovery)
else
  suites=("$suite")
fi
for group in "${suites[@]}"; do
  if run_suite "$group"; then :; else status=1; fi
done
git add -f local-tests-${HASH} && git commit -am "Local test run for ${HASH} [skip ci]" && git push
printf 'finished_utc=%s\n' "$(date -u +%FT%TZ)" >> "$RUN/environment.txt"
printf '\nResults: %s\n' "$RUN"
cat "$RUN/summary.tsv"
printf '\nLocal test results can be found in local-tests-%s\n\n' "${HASH}"
exit "$status"

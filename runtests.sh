#!/usr/bin/env bash
# Run from any directory; keep failures visible after packaging logs.
set -o pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")" || exit 1
if [[ -z "${VIRTUAL_ENV:-}" ]]; then
  source .venv-test/bin/activate || exit 1
fi
mkdir -p test-results || exit 1
status=0
python -m pytest -v -ra python/tests --ignore=python/tests/browser --ignore=python/tests/live_e2e \
  2>&1 | tee test-results/python.log || status=1
(
  for test in python/tests/test_*.js; do
    printf '\n=== %s ===\n' "$test"
    node "$test" || exit 1
  done
) 2>&1 | tee test-results/javascript.log || status=1

if python -u python/tests/check_browser_environment.py \
    2>&1 | tee test-results/browser-preflight.log; then
  python -m pytest -v -ra python/tests/browser \
    2>&1 | tee test-results/browser.log || status=1
else
  printf '%s\n' 'NOT RUN: browser preflight failed; see browser-preflight.log. This is a failed run, not a pass.' \
    | tee test-results/browser.log
  status=1
fi

# The live integration suite is separate and opt-in; missing prerequisites fail it.
if [[ "${LG_RUN_LIVE_E2E:-0}" == "1" ]]; then
  python -m pytest -v -ra python/tests/live_e2e \
    2>&1 | tee test-results/live-e2e.log || status=1
else
  printf '%s\n' 'NOT RUN: live E2E is opt-in; use LG_RUN_LIVE_E2E=1 bash runtests.sh.' \
    | tee test-results/live-e2e.log
fi

HASH=$(git rev-parse --short=7 HEAD 2>/dev/null) || HASH=unversioned
# Preserve the existing concatenated gzip/base64 result format.
if ! gzip -c test-results/* | base64 > "test-results.${HASH}.txt"; then
  status=1
fi
exit "$status"
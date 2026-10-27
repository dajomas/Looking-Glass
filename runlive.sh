#!/usr/bin/env bash
# Invoke with bash runlive.sh; no executable-bit change is required.
set -o pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")" || exit 1
if [[ -z "${VIRTUAL_ENV:-}" ]]; then
  source .venv-test/bin/activate || exit 1
fi
mkdir -p test-results || exit 1
python -m pytest -v -ra python/tests/live_e2e "$@" \
  2>&1 | tee test-results/live-e2e.log
exit "${PIPESTATUS[0]}"

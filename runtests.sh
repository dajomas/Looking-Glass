(
  source .venv-test/bin/activate

  set -o pipefail
  mkdir -p test-results
  rm -rf test-results/*
  
  status=0

  python -m pytest -ra \
    python/tests --ignore=python/tests/browser \
    2>&1 | tee test-results/python.log || status=1

  (
    for test in python/tests/test_*.js; do
      printf '\n=== %s ===\n' "$test"
      node "$test" || exit 1
    done
  ) 2>&1 | tee test-results/javascript.log || status=1

  python -m pytest -ra python/tests/browser \
    2>&1 | tee test-results/browser.log || status=1

  exit "$status"
)

BRANCH=$(git rev-parse --abbrev-ref HEAD)
git rev-parse ${BRANCH}
HASH=$(git rev-parse ${BRANCH} | cut -c1-7)

gzip -c -r test-results | base64 > test-results.${HASH}.txt
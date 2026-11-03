## Double-reveal regression checks

`python/tests/test_double_reveal.py` exercises room-only compositing, fog independence,
geometry invalidation, optimistic room revisions, navigation prerequisites and state preservation,
SQLite persistence, deleted destinations, portable backups, schema-15/16 compatibility,
duplication, checkpoint compatibility and history recovery. The file contains 15 cases including
parameterized legacy versions. `python/tests/test_double_reveal.js` exercises the real controller
with mocked DOM/transport plus the production selection interceptor. Existing click-handler
mocks now declare the new controller; browser render fixtures include its partial.

`python/tests/test_double_reveal_web.py` adds HTTP ownership/CSRF, image dimensions/previews,
stale-write and navigation checks. It skips when FastAPI is unavailable; a skip is not a pass.
Browser execution requires an installed Playwright Chromium. Run browser tests separately from
unit tests because several test module basenames overlap in the existing repository.

```sh
PYTHONPATH=python python -m pytest -q --ignore=python/tests/browser
for test in python/tests/test_*.js; do node "$test" || exit 1; done
PYTHONPATH=python python -m pytest -q python/tests/browser
python -m compileall -q python
```

The delivery-specific results, exact scope and unrun checks are recorded in
`Patch/VALIDATION.md`. No HTTP, browser, live deployment or Python 3.14 result should be inferred
from source compilation or mocked JavaScript tests. Migration expectations use `len(MIGRATIONS)`
rather than obsolete literals; the help CSS test is restricted to its intended six-rule block.


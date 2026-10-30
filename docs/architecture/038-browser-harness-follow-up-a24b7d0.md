## Browser harness follow-up (a24b7d0)

Browser tests share one session-scoped synchronous Playwright/browser lifecycle
from python/tests/browser/conftest.py. Do not re-export browser from test modules
or start overlapping drivers. Function cleanup closes leftover contexts after
failed setup; the batch fixture closes its page and local HTTP server in finally.
Batch readiness uses initialized controls with aria-busy=false, not a Ready
message. Result checks use separate map/source/failure/editor-warning counts
and verify Apply never calls window.confirm. Production behavior is unchanged.

Run python -m pytest --setup-plan -q python/tests/browser to check fixture
resolution (not UI execution), then python -m pytest -ra python/tests/browser.
Measured results and limitations are recorded in Patch/.



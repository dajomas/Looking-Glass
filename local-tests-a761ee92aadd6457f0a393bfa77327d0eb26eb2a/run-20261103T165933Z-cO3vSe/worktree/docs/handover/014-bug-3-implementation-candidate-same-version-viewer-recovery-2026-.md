## Bug 3 implementation candidate: same-version viewer recovery (2026-10-29)

Prepared against features/perplexity at 685fff20ebd63c6cb8abf4f36731ca72b327d682.
Bug 1 was delivered in 253b33ddae49d403a3985bf99135ce07226e95e4 and its TODO
completion was recorded in 685fff20ebd63c6cb8abf4f36731ca72b327d682. Earlier
candidate/open wording above records historical preparation, not current status.
Bug 3 remains open pending approved GitHub delivery; record its actual SHA then.

Scope: static/js/viewer_display.js adds a visible-stage condition to the
same-version fast path. An error-hidden stage reuses the normal decode/install
path instead of falsely reporting ready. Existing generation guards, blanking,
remote/local navigation, permissions and server play state are unchanged.
web_html/viewer/display.html bumps the display-script query token to
viewer-state-recovery-1. The existing viewer-refresh Node harness adds HTTP-error
injection and captured status reports; its original five tests are retained.
No changes to Python runtime code, migrations, routes or other backlog items.

Validation executed with Node v20.20.1:
- Expanded viewer-refresh suite before the fix: 3 failed, 7 passed (expected red).
- The same suite after the fix: all 10 passed, none skipped/cancelled.
- All 27 top-level JavaScript regression scripts passed after supplying their
  unmodified template fixtures; an earlier partial extraction lacked fixtures.
- node --check passed for the changed controller and regression script.
- The modified viewer template parsed with Jinja2; this is not browser rendering.

New coverage: HTTP 500/404 followed by same-version recovery; failed/loading/ready
status ordering and stage visibility; a still-visible same-version fast path;
blank response after an error; and a late recovery decode superseded by a newer
map. HTTP responses and WebSocket reports in these tests are mocks. No Python,
real HTTP/WebSocket, browser or live multi-viewer tests were run for this change.
The recovery logic adds no mutation calls; its final image/version checks still
come from the existing server endpoints. No implementation was pushed at preparation.


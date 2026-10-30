### 3. Viewer stays blank after a transient state error
- [x] Complete; delivered on `features/perplexity`.
- Fix commit: `b162dfca0e502f07a2d20ef7b654b7f9e19f3ee4`.
- Location: `static/js/viewer_display.js`, refresh().
- Validation: all 10 viewer-refresh tests and all 27 top-level JavaScript
  regression scripts passed with Node v20.20.1. Transport and DOM behavior were
  mocked; real HTTP/WebSocket, browser and live multi-viewer acceptance remain
  unexecuted. No application tests were rerun for this documentation update.
- Problem: failure hides the stage; a same-version retry returns early as ready.
- Solution: the same-version fast path now requires a visible stage; otherwise
  reload, decode and install the current image before reporting ready.
- Test: loaded map -> HTTP 500 -> same-version success restores image/status
  without a DM mutation; stale-response protection remains.


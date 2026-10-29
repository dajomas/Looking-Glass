## Bug 1 implementation candidate: inward fog feathering (2026-10-28)

Prepared against features/perplexity at ee9a0fa9d7f4a4fa4930d7217cd951dfbf899742.
Only services/fog.py and the new python/tests/test_fog_privacy.py change runtime
code/test coverage; README.md and this handover describe the same scoped fix.
The other 14 backlog items, database migrations, routes, assets and configuration
are unchanged. TODO item 1 remains open until approved GitHub delivery; record the
actual delivered SHA then. No GitHub implementation write has occurred at preparation.

The boolean mask now clips dilation to revealed interiors or wall pixels. Viewer
mask scaling uses nearest-neighbour support; Gaussian feathering is clipped to
that support so it softens inward only. The cache identity changes from
fog-cache-v2 to fog-cache-v3-inward-feather. Existing work-resolution/raster limits
remain; no whole-map source-image resampling redesign is included.

Validation executed with Python 3.14.4, using existing pure-Python pytest 8.3.5
sources through a temporary support path with plugin autoload disabled:
- New regressions on unchanged renderer: 13 failed, 2 passed (expected red run).
- New plus existing fog tests after the fix: 25 passed.
- Focused fog/doors/arrows/regions/double-reveal/passages/transitions suite:
  246 passed in the final run (3.62 seconds).
- Broader 64-module non-HTTP suite: 574 passed, 2 failed. Failures are the stale
  scrying-auto-2 template assertion and viewer-sync equal-timestamp history eviction.
  Both were reproduced from untouched baseline sources; neither is fixed here.
- All 192 Python sources compiled with Python 3.14.4.

Exact pixel assertions use PNG and cover default feather radius 2, radii 0/5,
mask upscaling/viewer downscaling and odd dimensions, wall dilation, full reveal,
full hide and restart isolation from old disk caches. JPEG/WebP visual output,
HTTP endpoints, browsers and live multi-viewer behavior were not executed.
FastAPI/Uvicorn remain unavailable; compilation/service tests do not substitute
for those checks. Do not claim the broad suite passed or relax unrelated tests.


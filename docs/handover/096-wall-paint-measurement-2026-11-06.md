# Wall-paint screenshot measurement correction (2026-11-06)

## Scope and preserved failure

CI run 42113616342 attempt 1 tested a54f6346ff6fa2b89b94c719f9bc5e89b0483559
and failed the battle variant of test_keyboard_width_zoom_and_reload: measured
paint width 0 before zoom and 8 afterward. Browser totals were 171 passed/1
failed; the other four jobs passed. Same-SHA local evidence passed all five
suites. Preserve both results; no rerun or this correction retroactively changes
the failed CI result. The evidence did not retain the failing screenshot/trace,
so the original zero's exact timing remains unproved.

The source has a locator/measurement window and a separate coordinate/screenshot
window while startup refresh can replace SVG paths. Record 042 documents prior
detached-path experiments, not proof of this particular screenshot failure.

## Correction

Only tests and handover documentation change. A new wall_paint_support helper
queries the current path, connectivity, CTM, CSS width, visibility, clipping
viewport and strip coordinates in one JavaScript execution. Per-node identity,
document identity and scoped SVG/ancestor mutation tracking join the geometry
in before/after screenshot samples. Changed samples retry within a five-second
measurement deadline; the test itself is not rerun. Screenshots provide paint
opportunities without fixed sleeps. CSS-scale screenshots must match CSS viewport
dimensions, and the whole 31-pixel strip must be inside the visible map viewport.

A sample requires positive magenta coverage and computed screen width within
0.01 px of the requested setting. Its supplemental absolute paint credibility
band is max(1, floor(expected)-2, minimum) through ceil(expected)+1 strong-colour
pixels, allowing antialiased edges without accepting zero. The original zoom
difference tolerance stays +/-1 px. Native-drag growth remains at least four
pixels while the thumb is held; reload now also verifies painted width. Label,
persistence, no-POST and no-page-error assertions remain. Production SVG/CSS,
startup refresh, fog guard, workflows and permissions are unchanged.

On timeout the helper attempts PNG/JSON diagnostics in test-results/wall-paint/,
with unique names and last sample/error/width information. The existing CI upload
already includes test-results/. Diagnostic write/capture failures remain visible
in the assertion; they cannot turn failure into success. These are runtime test
artifacts, not files committed to the repository. No archive or Patch/ is added.

## Executed validation and limits

The reconstructed original browser test matched Git blob
344ed648c5fadb9da34fd47d30fe8bc8c017698d before editing. Python source parsed;
the JavaScript probe parsed under Node. Thirteen actual pytest helper regressions
passed in an isolated sandbox copy (final run 0.23s), using synthetic PNGs/page
doubles. They cover acceptance, zero/wrong-width/missing/clipped/unstable/zoom/
viewport rejection, changed-sample retries, diagnostic files and native growth.
These checks do not execute the DOM probe in Chromium or the real editor.
Full browser/application/CI suites were not run by the assistant. Browser
validation remains required; no claim the original CI cause was reproduced.

Reviewed README.md and HANDOVER.md; README remains accurate without cosmetic
changes. HANDOVER links this record. Changed code files are 5,869, 3,263 and
6,494 UTF-8 bytes, all below 25,000; documentation also stays below that limit.
Bug 28 is not accepted/closed here; earlier evidence/history remains unchanged.
The commit has no [skip ci]. Report its actual SHA only after the approved write.

## Next validation

```bash
python -m pytest -q python/tests/test_wall_paint_support.py
python -m pytest -q python/tests/browser/test_wall_width_followup.py
```

Run normal CI too. Inspect PNG/JSON diagnostics if convergence still fails; do
not increase the +/-1 tolerance or suppress genuine rendering failures. Stable
before/after probes cannot make screenshots and DOM sampling literally atomic
or establish correctness for every transient compositor/browser condition.

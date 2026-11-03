## Fixture repair and UI follow-up for 9f3be8f

`python/tests/browser/browser_support.py` provides an override-first Jinja
ChoiceLoader with real web_html/templates fallback. Shared partials must not
be replaced with empty strings merely to hide missing-template errors. The
auxiliary GET helper handles only named independent room-note, double-reveal
and transition endpoints; it never swallows writes or unknown requests.

Gesture fixtures now render the actual map-editor template instead of a drifting
minimal DOM. This preserves production prerequisite order, controls and real
PanZoom/editor behavior. The viewer-centering fixture explicitly includes
viewer_area_zoom.js before viewer_display.js. Optional independent API responses
have bounded empty schemas; the tested metadata/actions remain fixture-controlled.

The source busy assertion uses the intended Uploading / processing message,
retaining original scene-index and exact assignment-payload checks. Empty sources
must show No wall sets found and keep Apply disabled. Production inspect() now
distinguishes that empty state.

Batch clock tests install and pause virtual time before loading the application,
then use run_for(3999) and run_for(1). No real setup/polling time is allowed to
consume the four-second deadline. Geometry tests pan the image edge into the
viewport and assert hit-testing reaches it before using a real pointer click.
Do not replace pointer tests with synthetic callbacks or force=True.

Floating-dialog content growth is observed with ResizeObserver; reflow preserves
the current/user-dragged position when possible and clamps it when necessary.
A regression adds secret controls and checks bounds plus ordinary Apply/Close
clicks. Browser-free Node coverage checks dynamic growth and cleanup.

The zoom-2.5 label screenshot assertion remains strict. On failure it saves the
screenshot and coordinates under pytest's tmp_path. Its threshold was not relaxed;
that visual issue may remain platform-specific and requires target-host review.

Focused commands from repository root:

```sh
python -m pytest -q python/tests/test_browser_fixture_support.py
node python/tests/test_floating_dialog_reflow.js
python -m pytest -v python/tests/browser/test_saved_wall_sources.py
python -m pytest -v python/tests/browser/test_ui_refinement.py
python -m pytest -v python/tests/browser/test_secondary_click.py
python -m pytest -v python/tests/browser/test_portal_tools.py
python -m pytest -v python/tests/browser
```

The supplied baseline has 31 failures and 13 setup errors, often grouped behind
one fixture defect. A repaired fixture can expose additional assertions; do not
count those earlier setup failures as validated features. Patch/ contains exact
new execution results and distinguishes them from target-host baseline evidence.



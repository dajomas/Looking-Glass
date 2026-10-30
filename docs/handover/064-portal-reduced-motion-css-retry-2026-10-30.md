# Portal reduced-motion computed-style synchronization (2026-10-30)

Prepared against features/perplexity 02cfae96bfc98d71dd9b8fc2ed0d4966781a9c37. Run 41128592368 tested 8652625c4be6a322edd322807cc8598f97cda522. Python/HTTP, JavaScript, live Uvicorn and Recovery jobs succeeded; browser execution reported 171 passed and one failure: test_admin_viewport_visibility_and_reduced_motion read an empty computed animationName instead of none. All three retained-note recovery UI tests passed in that run.

Source review confirms portal_cycle.js registers a reduced-motion media change listener that refreshes the overlay, and render() calls replaceChildren() before inserting new polygons. Waiting for polygon count alone does not synchronize a one-shot element.evaluate style read with that refresh. The test now uses the live locator's retrying to_have_css("animation-name", "none") assertion. The exact required value is unchanged; empty or animated values remain failures. The existing two-polygon, offscreen-removal, fit-return and no-write assertions are preserved. No fixed sleeps, timeout increases, skips, production code/CSS, fixture changes or workflow changes are included.

README.md and HANDOVER.md were reviewed. No user-facing documentation changes are necessary for this test-only correction; this focused record captures the decision and pending validation. Existing archived records/manifests and evidence are unchanged.

Validation: source review only. No new pytest collection, Chromium execution, repeated stress runs or CI result was executed/verified here. Run from repository root with development and Playwright dependencies installed:

```bash
PYTHONPATH=python python -m pytest -v -ra python/tests/browser/test_portal_tools.py -k test_admin_viewport_visibility_and_reduced_motion
PYTHONPATH=python python -m pytest -v -ra python/tests/browser/test_portal_tools.py
PYTHONPATH=python python -m pytest -v -ra python/tests/browser
```

Repeat the focused case across fresh invocations and inspect full integration evidence for the delivered SHA. The source explains a plausible race, not an experimentally reproduced root-cause trace; if bounded retries still fail, investigate actual rendering instead of weakening expectations. Bug 2 final documentation and disposable-upgrade acceptance remain separate unfinished work. No archive-only Patch/ material is committed.

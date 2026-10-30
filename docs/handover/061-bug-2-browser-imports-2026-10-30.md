# Bug 2: browser conftest helper imports (2026-10-30)

Prepared against features/perplexity e72e803aa3c5375722d28c4fbe48f186cb863112. Run 41119516103 tested bf6661cd8af1be13a3004e524e2725c937b70782: Python/HTTP, JavaScript, Live Uvicorn and Recovery jobs succeeded; the browser job stopped during collection because test_web imported png_bytes from the browser conftest. The supplied local four-module run reported 32 passed. These are previous-source results, not validation of this increment.

The shared png_bytes and two_room_scene implementations move unchanged to python/looking_glass_test_helpers.py, a uniquely named test-support module outside the application package. Root and browser conftests re-export the same function objects so existing from-conftest imports remain compatible whichever conftest pytest binds by name. The parent conftest retains application-path initialization and settings/scene fixtures. Browser launch, cleanup and the pre-existing dependency importorskip are unchanged. No sys.modules or import-order workaround is added to production fixtures.

New top-level regressions load both conftests under distinct names, temporarily bind each to conftest, and freshly import the real test_web module. They check helper identity and fixture importability without invoking Chromium. A separate builder regression checks PNG dimensions/pixels and scene wall/door geometry. Test-local sys.modules/path changes are restored by monkeypatch. These checks are not substitutes for actual browser collection and execution.

README.md and HANDOVER.md were reviewed. README behavior remains unchanged. This focused record contains scope, validation limits and unfinished work; no historical archive or manifest is rewritten. No production routes, UI assertions, workflow selectors, exclusions or new skips change.

Validation: source review only. No pytest collection, new unit tests, Chromium tests or new workflow results were executed/verified here. With development and Playwright dependencies installed, run from repository root:

```bash
PYTHONPATH=python python -m pytest -v python/tests/test_conftest_helper_imports.py
PYTHONPATH=python python -m pytest --collect-only -q python/tests/browser
PYTHONPATH=python python -m pytest -v -ra python/tests/browser/test_room_note_recovery_ui.py
PYTHONPATH=python python -m pytest -v -ra python/tests/browser
```

Then rerun/review full integration checks for the delivered source SHA. Collection repair may expose previously unexecuted browser assertion failures; none are hidden or claimed resolved. Bug 2 acceptance remains open. No downloadable archive was requested and no Patch/ material is committed.

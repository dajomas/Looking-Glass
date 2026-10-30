## Items 7 and 8: import busy feedback / access logging

Commands:

```sh
PYTHONPATH=python python -m unittest discover -s python/tests -p test_access_logging.py -v
node --test python/tests/test_*.js
python python/tests/check_upload_busy_browser.py
```

The optional browser regression requires Playwright and an installed Chromium;
neither is a runtime application dependency. It intercepts a delayed real native
multipart POST and checks duplicate suppression, preserved file/CSRF/submitter
fields, visible feedback, validation/confirmation cancellation, JS-managed form
exclusion and back-forward restoration. Logging tests cover success filtering,
4xx/5xx retention, warning retention, unknown formats, opt-in and idempotent setup.
Room-note DOM regressions now check busy feedback and repeat-upload blocking.

Patch-environment results: seven logging unittests, 33 Node test-runner cases and
seven browser checks passed. Changed Python syntax, JavaScript syntax, Jinja
compilation and archive integrity/hash checks also passed. FastAPI and Uvicorn
are unavailable here, so full application integration and live Uvicorn log output
were not exercised. Target Python 3.14 and cross-browser acceptance remain open.

Installation acceptance:
1. With network throttling, import a large map and click/press Enter repeatedly.
   Verify one import, immediate busy feedback and normal success/error redirects.
2. Repeat for image replacement, backup inspection/restore, saved wall sources,
   batch maps/walls and room-note imports. Check error recovery and Back navigation.
3. Confirm the full-width duplication panel layout remains unchanged.
4. Verify normal 200/303/304 HTTP requests are quiet; intentional 404/422 failures
   are logged at INFO, and application/server failures retain their diagnostics.
5. Set access_log_success true, restart and verify successful access lines return.


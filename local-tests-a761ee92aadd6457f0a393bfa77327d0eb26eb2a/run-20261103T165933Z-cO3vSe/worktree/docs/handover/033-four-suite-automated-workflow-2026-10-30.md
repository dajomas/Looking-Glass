## Four-suite automated workflow (2026-10-30)

The existing integration workflow now includes Python / HTTP, JavaScript
regressions, Browser / mocked HTTP and Live Uvicorn as independent matrix jobs.
The existing two check names are retained. All jobs use Python 3.14, and the
JavaScript job additionally configures Node.js 24. Browser/live jobs install
Playwright Chromium with system dependencies and require the existing bounded
browser environment check. Strict nonempty/no-failure/no-reported-skip JUnit
validation and always-uploaded per-suite artifacts remain enabled. Evidence
identity is initialized before dependency installation. No branch protection
settings were changed: administrators must require all four checks separately.

The new `tools/run_javascript_tests.py` discovers every top-level test_*.js,
continues after script failure, logs each script, records status/duration inventory
and emits one JUnit case per script. It fails on empty discovery, missing Node,
nonzero exits or a default 120-second per-script timeout. Nested Node case/skip
semantics are not parsed; script exit status is the contract. Existing tests
and local JavaScript loop are unchanged. A small pytest adapter includes the
existing standalone upload-busy Chromium check in browser discovery without
changing its assertions; local browser-suite execution also discovers it.

The live getworkflow.sh was reviewed and left unchanged: it already downloads
all artifacts for the selected run and prepares reading chunks for all files.
No extra evidence upload/download action, new archive or runtime change is needed.
README's CI overview now links to `docs/ci-tests.md`, the current four-suite
contract. That focused guide supersedes old CI-specific descriptions in the
oversized docs/testing.md while leaving historical/general/manual content intact.
Discovery covers existing automated groups, not arbitrary future standalone
filenames, manual acceptance, other operating systems or other browser engines.

Validation performed locally: workflow YAML parsing/matrix structure checks and
five isolated JavaScript-runner smoke scenarios (success, continuation after
failure, timeout, empty discovery, missing executable). Runner fixtures used
Python as the stand-in subprocess, not Node or project JavaScript tests.
No full checkout test run, actual Node suite, Chromium test, hosted Actions run,
or actionlint validation was performed. First four-suite CI acceptance is pending.
The prior two-suite run 41014901375 against 977f65a390586e8b7262380e0ba3acd678cb4bf4
was reviewed as successful (1,125 Python tests, 29 subtests, four live tests);
that result does not establish the newly included suites pass.


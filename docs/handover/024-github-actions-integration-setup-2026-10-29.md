## GitHub Actions integration setup (2026-10-29)

Documentation baseline: `75bbe528e4745b523f96fba3d0b6debe7b0caf4e`
(`Add test workflow`). That commit adds
`.github/workflows/integration-tests.yml`. These documentation additions do not
change application code, dependencies, migrations, tests or workflow behavior.
Existing documentation and historical validation records are retained.

The workflow defines separate `Python / HTTP` and `Live Uvicorn` checks using
Python 3.14 on Ubuntu. Both install development/runtime dependencies and perform
hard imports of FastAPI, Starlette, Uvicorn, python-multipart, HTTPX and pytest.
The live job additionally installs Playwright and Chromium with system libraries
and enables `LG_RUN_LIVE_E2E=1`.

The Python check excludes `python/tests/browser` and `python/tests/live_e2e`.
The live check selects `python/tests/live_e2e`. In-process ASGI coverage must not
be described as Uvicorn listener coverage. An import preflight is not request
parsing coverage: HTTP tests must exercise actual forms and multipart uploads.
Similarly, live startup alone does not establish graceful-shutdown coverage.

The workflow preserves pytest exit failures through shell pipelines and audits
JUnit output. Missing reports, zero reported cases, failures/errors and skipped
cases fail acceptance. Expected failures represented as skips are rejected too;
review deliberate skips explicitly rather than silently permitting missing
integration coverage. Artifact evidence includes the checked-out SHA, environment,
installed packages, dependency preflight, pytest log and JUnit report.

Status at documentation preparation: workflow existence verified by commit
metadata; no Actions run, test outcome, artifact, branch rule or required-check
setting was verified. No tests were executed for this documentation update.
Earlier pending ASGI/deployment acceptance is not cleared by adding CI files.
Standalone JavaScript and the mocked-browser suite are outside these two checks.
Ubuntu CI does not establish Windows or other deployment-platform acceptance.

Next acceptance steps:
1. Inspect an Actions run for the exact revision containing these changes.
2. Resolve failures without hiding required integration tests behind skips.
3. Record run URL, tested SHA, job results, test counts and unresolved limitations.
4. Configure the displayed checks as required in the intended destination branch's
   ruleset/protection settings, subject to repository permissions and availability.
5. Use a pull-request gate when validation must precede entry into a protected
   branch; a direct-push workflow validates only after that push has happened.

No GitHub commit or push is performed by the local documentation generator.
Record the actual delivery SHA only after delivery succeeds. Do not add generated
supporting delivery material to the repository unless explicitly intended.

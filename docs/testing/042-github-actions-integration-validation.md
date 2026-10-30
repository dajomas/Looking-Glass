## GitHub Actions integration validation

The workflow is `.github/workflows/integration-tests.yml`. It is configured for
pushes to `features/perplexity`, pull requests and manual dispatch. Manual dispatch
visibility/availability depends on GitHub's workflow/default-branch rules; a push
is sufficient to trigger the configured branch workflow. The actual YAML remains
authoritative if its configuration is changed later.

### Check scope

| Check | Selected tests | Coverage boundary |
|---|---|---|
| Python / HTTP | `python/tests`, excluding `browser` and `live_e2e` | Services and in-process HTTP/WebSocket integration; not real Uvicorn listeners |
| Live Uvicorn | `python/tests/live_e2e` | Live application listeners and the scenarios implemented in that suite |

Both jobs use Python 3.14 and install `requirements-dev.txt`, which includes
runtime requirements. The live job installs Playwright and Chromium with OS
libraries. These checks do not run standalone JavaScript regressions or the
separate mocked-browser suite. Those remain additional validation obligations.
Ubuntu results do not establish Windows, other operating-system or target-host
acceptance. Passing tests establish only their asserted scenarios, not every
behavior of FastAPI, Starlette, Uvicorn or python-multipart.

### Dependencies and failure policy

The preflight imports `fastapi`, `starlette`, `uvicorn`, `python_multipart`,
`httpx` and `pytest` and records their distribution versions. A missing required
dependency fails the job, rather than becoming optional skipped coverage.
`pip check` verifies installed dependency consistency.

A required job fails on pytest failure, missing JUnit output, zero reported test
cases, or any reported skipped case. The JUnit audit includes collection-time
module skips represented in that report. Expected failures represented as skips
also fail this strict policy. Existing intentional platform skips must be reviewed
explicitly; do not add a blanket bypass or `continue-on-error`.

Hard imports are prerequisites, not behavioral coverage. Multipart acceptance
requires real form/file-upload requests through the application. HTTP/WebSocket
acceptance requires real ASGI tests, not AST route-body tests or socket doubles.
Uvicorn acceptance requires live listener tests. Shutdown acceptance requires
explicit shutdown assertions, not merely successful startup.

### Equivalent local suite commands

Run from the repository root in a dedicated Python 3.14 virtual environment:

```bash
python3.14 -m venv .venv-test
source .venv-test/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python -m pip check
mkdir -p test-results

PYTHONPATH=python python -m pytest -v -ra python/tests \
  --ignore=python/tests/browser \
  --ignore=python/tests/live_e2e \
  --junitxml=test-results/python.xml

python -m pip install playwright
python -m playwright install --with-deps chromium
LG_RUN_LIVE_E2E=1 PYTHONPATH=python python -m pytest -v -ra \
  python/tests/live_e2e --junitxml=test-results/live.xml
```

The Playwright system-library installation can require administrator privileges
on supported Linux hosts. The commands select the same suites but do not by
themselves reproduce the workflow's dependency-import preflight and strict JUnit
no-skip audit. Inspect skips locally or run the same audit as the workflow before
claiming equivalent strict acceptance. Preserve nonzero pytest exit status when
piping output through `tee` by enabling `set -o pipefail` in Bash.

### Evidence and first-run review

In the repository's Actions tab, open the workflow run for the intended revision.
Inspect both checks and their dependency preflight, test output and JUnit audit.
Artifacts are named `integration-python-<SHA>` and `integration-live-<SHA>` and
are configured for 14-day retention, subject to repository/organization policy.
Each job attempts artifact upload even after failure. Setup failure can mean some
or all result files do not exist; absence of evidence is not a passing result.

Evidence files under the artifact's `test-results` content include:

- `environment.txt`: checked-out commit SHA, Python/pip versions and platform.
- `installed-packages.txt`: installed distribution versions from `pip freeze`.
- `dependency-preflight.txt`: required integration package import/version output.
- `pytest.log`: pytest output.
- `results.xml`: JUnit test results.

For pull requests the checked-out SHA can identify GitHub's test merge commit;
retain that SHA and the PR head SHA when tracing results. Package versions are
recorded for traceability; lower-bound requirement ranges are not a dependency
lock and do not guarantee identical future resolutions.

Record the run URL, tested revision, counts, failures/skips and limitations after
execution. Workflow installation, compilation or successful collection alone
must not be reported as integration acceptance.

### Require checks before merging

After a run has registered the checks, configure the intended destination branch's
ruleset or branch protection to require the exact displayed `Python / HTTP` and
`Live Uvicorn` status checks. If validation must precede entry into that branch,
require pull requests and restrict bypasses as appropriate. Availability depends
on repository settings, permissions and plan. Defining YAML alone does not
configure branch protection.

A push directly to `features/perplexity` starts validation after the commit is
already on that branch; it is not a pre-push gate. Do not change other branches
or repository rules without the owner's explicit approval.

### Setup status

The workflow was added in commit
`75bbe528e4745b523f96fba3d0b6debe7b0caf4e`. These documentation additions do
not assert a successful Actions run or verified required-check configuration.
No tests were executed while preparing these documentation additions.

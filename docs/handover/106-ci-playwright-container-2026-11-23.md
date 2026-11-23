# CI: browser and live jobs in the Playwright container image (2026-11-23)

## Why

Run 45179421782 took 7 min 27 s against about 3 min before. Its test steps took
their usual time; "Install browser dependencies" (`playwright install --with-deps
chromium`) took 347 s in the browser job and 170 s in the live job because the
runner's Ubuntu mirror served font packages at about 50 kB/s. The user asked to
move those jobs into the container image.

## Change (`.github/workflows/integration-tests.yml`)

- Matrix entries for Browser / mocked HTTP and Live Uvicorn set
  `container: {image: mcr.microsoft.com/playwright:v1.65.1-noble, options:
  --ipc=host}`; the job uses `container: ${{ matrix.container }}`, so the
  Python, JavaScript and Recovery entries still run on the runner (Recovery
  needs the runner's Docker).
- The image is the general Playwright image (Ubuntu 24.04, browsers in
  `/ms-playwright`, all system packages). A matching Python-variant tag for the
  package version CI used (1.65.2) could not be confirmed from here; Python 3.14
  still comes from `actions/setup-python`.
- Install step: `pip install "playwright>=1.65,<1.66"` and `playwright install
  chromium` without `--with-deps`. No apt downloads; a browser build is fetched
  only if the package's revision differs from the image's.
- `PYTHONPATH` moved from the job `env` (which used `${{ github.workspace }}`,
  the host path, wrong inside a container) to `$GITHUB_WORKSPACE/python` written
  to `GITHUB_ENV` in the first step, correct on the runner and in containers.
- `environment.txt` records `$GITHUB_SHA` instead of `git rev-parse HEAD` (the
  image may lack git) and the container image used.
- `docs/ci-tests.md` describes the setup and the version-alignment rule.

## Validation

YAML parse and matrix resolution checked locally. The first push of this change
runs CI and is the evidence; see the end of this record once recorded.

## First container run and fix

Run 45182485974 (`b9a64e2`): Python, JavaScript and Recovery passed on the
runner; both container jobs failed in Set up Python with `spawn
/__t/Python/3.14.10/x64/bin/pip ENOENT`. setup-python reused the runner's tool
cache, mounted at `/__t` in the container, whose scripts carry host shebangs.
A first fix overriding `RUNNER_TOOL_CACHE`/`AGENT_TOOLSDIRECTORY` for the step
had no effect (run 45183128048, same error). Only setup-python's pip-cache
lookup runs the `pip` script; the workflow's own steps use `python -m pip`. The
container jobs now set `cache: ''` (expression
`matrix.container && '' || 'pip'`); runner jobs keep the pip cache.

# Current validation report

Base: `b04a92468ad47d0a2c618b18035a7d345c402704`, using the user-supplied base64 source ZIP.
The source ZIP was decoded locally; it was not independently compared with GitHub.

## Executed

- 41 pytest tests passed across test_foundry_import, test_fog,
  test_wall_sources_repository, test_pack_images and test_wall_types.
- Includes v1 and v2 database upgrades, idempotent migration 3, independent
  category filtering, non-destructive stored walls, fog room merging,
  actual viewer rendering from the same canonical map image, Foundry data URIs,
  thumbnail labelling, Universal VTT base64 images, ZIP relative artwork paths,
  path traversal rejection, size-limit and malformed-base64 rejection, and
  animated image normalization to one frame.
- Every application Python file parsed with ast.parse (Python 3.12).
- node --check passed for both changed editor JavaScript files.
- bash -n run.sh passed.
- Real supplied maps.db parsed by the updated importer: 13 wall sets;
  image availability/reference summary is included alongside this report.
- Generated unified patch was checked against the supplied baseline using
  git apply --check (result recorded during packaging).

## Not executed

FastAPI is not installed in the packaging environment. The full HTTP suite,
including test_pack_images_web.py, has NOT been run. Browser interactions,
WebSocket live refresh and real Windows Batch/PowerShell execution have NOT
been run. Dependency installation/startup was not run (no network access).
There is no claim of complete end-to-end validation or native Windows testing.
The wrappers follow the requested run.* pattern; Scrying Glass launcher source
was not supplied and these are not claimed to be exact copies of its behavior.

## Run after applying

```bash
./run.sh --install --help
.venv/bin/python -m pip install -r requirements-dev.txt
cd python
../.venv/bin/python -m pytest -q
```

Manually: choose embedded full art, keep uploaded art, and choose thumbnail;
compare DM artwork to a fully revealed viewer of the SAME ACTIVE map. Check
replacing same-size art in two browser sessions, changing dimensions, each wall
Show/Enabled switch, door master switch, fog reset and source deletion. Check
all three launchers from directories containing spaces and with config/env
port overrides. Back up persistent data before migration 3.

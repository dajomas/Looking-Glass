# Apply the reusable wall-source feature

Base: features/development at 3b485d96e44ed24c5593a2b8437255c02778a917.
This archive is a repository-root overlay of full changed/new files, not a full
repository and not a database backup. It also contains changes.patch for review
and application. Do not apply both the patch and overlay.

## Recommended: apply the unified patch

Extract the archive to a temporary directory, not directly over your checkout.
In your existing clean repository:

```bash
git switch features/development
git rev-parse HEAD
# Confirm: 3b485d96e44ed24c5593a2b8437255c02778a917
git status --short
# Confirm no local changes that would be overwritten.

# Substitute the actual extraction directory for /tmp/lg-wall-sources.
git apply --check /tmp/lg-wall-sources/Patch/changes.patch
git apply /tmp/lg-wall-sources/Patch/changes.patch
git diff --check
git diff --stat
```

Alternatively, after verifying the checkout and backing it up, copy the full
files from the extracted archive into the repository root, preserving paths.
Do not copy a second top-level directory around the existing repository.
manifest.json lists payload paths, SHA-256 checksums and original Git blob hashes.
Patch/changes.patch and manifest.json are packaging metadata and are not included
in the unified patch itself.

## Validate and start

Stop Looking Glass and back up its whole data directory before first restart.
Run tests against a disposable database; then start normally to migrate the
real database from schema 1 to 2. No configuration change or additional runtime
dependency is required. If containerized, rebuild the image with these files.

```bash
.venv/bin/pip install -r requirements-dev.txt
(cd python && ../.venv/bin/python -m pytest -q)
.venv/bin/python python/main.py
```

Read TEST_REPORT.md for checks performed here and tests still required. Run the
browser acceptance checklist before a live session. Save an image with maps.db,
then select a saved source and wall set in the editor; another map can choose
the same source without re-uploading. Sources are shared within a campaign only.

## Commit (local commands; no remote write was performed)

After tests and review, explicitly stage the feature's changed and new files,
then use the supplied commit message. If using the unified patch, the message
and patch notes are already in the checkout:

```bash
git add README.md docs/api.md docs/architecture.md docs/foundry-import.md docs/usage.md
git add python/looking_glass/db.py python/looking_glass/repositories/wall_sources.py
git add python/looking_glass/web/admin/api.py python/looking_glass/web/admin/campaigns.py
git add python/looking_glass/web/admin/wall_sources.py
git add static/js/wall_source_library.js web_html/admin/map_editor.html
git add python/tests/test_wall_sources_repository.py python/tests/test_wall_sources_web.py
git add Patch/README.md Patch/wall-source-library.md Patch/TEST_REPORT.md
git add Patch/COMMIT_MESSAGE.txt Patch/sample-database-summary.json
git commit -F Patch/COMMIT_MESSAGE.txt
```

For rollback, restore pre-upgrade code and the stopped-service data backup.
Do not manually decrement schema_version. The original user-supplied database
is not redistributed; only its scene names and document counts are included.

## Latest follow-up patch

The patch based on b04a924 adds optional shared pack artwork, wall-type controls
and portable launchers. See [the follow-up guide](image-wall-controls/README.md)
and [its validation report](image-wall-controls/TEST_REPORT.md).
`COMMIT_MESSAGE.txt` and `changes.patch` now describe that follow-up.
Earlier reports in this folder describe the earlier wall-source feature only.

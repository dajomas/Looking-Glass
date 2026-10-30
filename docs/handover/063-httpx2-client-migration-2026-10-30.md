# Complete live/recovery HTTP client imports (2026-10-30)

Prepared against features/perplexity d0d7bbcd1bfab82f34d179fa16bae501f8ae414e. Run 41127343497 tested c77d2820607c319be0f82ac7848a376e19595602: dependency preflight and Python/HTTP, JavaScript and browser jobs passed, but live/recovery collection failed on three remaining imports of the removed HTTP client distribution.

The three affected modules are python/tests/live_e2e/test_live_revocation.py, python/tests/recovery/test_restart.py and python/tests/recovery/test_container.py. Each now imports httpx2 as httpx. The local alias preserves existing Client, Cookies and HTTPError references without depending on or reinstalling the old package. Network/auth/cookie/redirect/file-upload/pixel assertions, timeouts, process/container isolation and cleanup are unchanged.

Reviewed current requirements and both workflow definitions: requirements-dev and regular dependency preflight already select httpx2; the focused workflow installs the same requirements. Inspected live fixture/support, checkpoint and ZIP restore modules and migration-interruption recovery test for deferred dependencies. README.md and HANDOVER.md were reviewed; no cosmetic edits are needed. Historical logs/handover archives and manifests are intentionally not rewritten, and aliases are not obsolete package imports.

GitHub indexed code search returned incomplete results; this session does not claim a completed exhaustive remote scan. The new top-level test_http_client_dependency.py audits every Git-tracked active Python file (including nested live/recovery helpers and embedded Python strings), requirements, workflow/config/build files and current documentation/scripts for recognizable old imports, literal deferred module names and install references. It excludes historical ci-results collections and dated handover/TODO archives, not active tests. Computed/obfuscated imports and arbitrary install wrappers are outside this static guard. Findings fail with filenames rather than silently skip. Scanner regressions cover direct, from, nested, dynamic and embedded imports; a non-network test checks the httpx2 Client/Cookies/HTTPError surface used by these suites. No production code, requirements, workflows, evidence or skips change.

Validation: source review only; httpx2 is not installed in the assistant Python workspace, and there is no live checkout there. No new regression, repository-wide audit, pytest collection, HTTP, Chromium, restart, Docker or CI execution is claimed. Run the following after delivery, then require all five integration jobs against the delivered SHA:

```bash
PYTHONPATH=python python -m pytest -v -ra python/tests/test_http_client_dependency.py
PYTHONPATH=python python -m pytest --collect-only -q python/tests/live_e2e python/tests/recovery
LG_RUN_LIVE_E2E=1 PYTHONPATH=python python -m pytest -v -ra python/tests/live_e2e
LG_RUN_CONTAINER_TESTS=1 PYTHONPATH=python python -m pytest -v -ra python/tests/recovery
```

Actual API compatibility, especially real redirects, cookies and multipart uploads, remains subject to those executions; changing an import or passing client construction is not proof. If the tracked-file audit reports further executable references, review and migrate them rather than weakening the guard. Bug 2 acceptance/documentation work remains open independently. No archive-only Patch/ material is committed.

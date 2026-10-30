# Deployment documentation test split alignment (2026-10-31)

Baseline: features/perplexity 03a95cda4e5826941a2a98195715d2693385f8a3.
README.md and HANDOVER.md were read from the live branch before preparation.

## Cause and correction

Retained CI run 41144347353, attempt 1, tested
c70d2cb7ec06e41193d04a50e5902d272e789769. Python/HTTP reported 1261 passed,
3 failed and 29 additional subtests passed. The failures were
test_container_paths_are_explicit, test_first_install_uses_production_example
and test_viewer_port_preserved. Each read docs/deployment.md as a monolithic
guide, but that file became a navigation index in the completed guide split.
The configuration default itself passed its 5100 assertion.

Update only the test input paths: the Podman assertions read section 005; the
installation assertions read sections 002, 005 and 007; viewer-port documentation
assertions read operational sections 002-005. This intentionally scopes the
port prose check to native installation, systemd, networking and Podman rather
than unrelated historical upgrade sections or the navigation index. Missing
files fail normally. Every existing assert expression is unchanged, including
the exact two-install-command count, all mounts/environment/user-namespace
requirements, migration/CLI guidance, runtime port and absence of port 6000.
No fallback, xfail, skip, workflow exclusion or runtime change is introduced.

## Actual preparation validation

The full original test modules were reconstructed and matched live Git blobs
65da65e0a67a11b33a9c4b5f066f6b0a8d921c7d and
4f7e2c42f2493b5cde51c35a8452a795eee3ac2c. Both complete candidates compiled
on Python 3.12. An AST comparison verified all assert expressions are preserved.
Candidate blobs are 38b688a2d730fac2d308f2f4048a193fd1535dd9 and
8280da4429cf42f5dc1c454db820e87f3e78a829 respectively. Relevant live section
files were reviewed, not edited. No pytest collection/execution, application
initialization or new CI run was performed during this preparation. Compilation
and source review do not establish passing tests. Run in a normal checkout:

```bash
PYTHONPATH=python python -m pytest -q python/tests/test_deployment_paths.py python/tests/test_sidebar_appearance.py
```

Review the new exact-SHA CI result after delivery; do not describe the earlier
failing run as green. Its other four jobs succeeded: JavaScript 28 scripts,
browser 172 tests, live 18 tests, recovery 6 tests. All 11 Bug 13 HTTP cases
passed in its Python log. The user's separate focused run reported 34 passed
in 22.09 seconds. These are historical evidence, not passes for this test edit
or final deployment/user acceptance of Bug 13.

## Documentation and queued workflow retirement

README.md remains accurate and needs no cosmetic change. HANDOVER.md gets only
a short pointer here. Deployment sections/indexes and all historical split
manifests remain unchanged. No Bug 2 closure or runtime implementation is reopened.

The user separately requested retirement of the standalone workflow named
Bug 2 regression execution: .github/workflows/bug-2-regressions.yml. That file
still exists at this preparation baseline. The connector's multi-file write
cannot express deletions, so removal requires its own exact-approved delete
commit. This test-fix commit does not remove it or claim retirement succeeded.
Preserve the regression tests, main five-suite integration workflow and
historical record 059; add a dated retirement/status note after actual deletion.
No other branch, merge, archive or Patch/ material is part of this change.

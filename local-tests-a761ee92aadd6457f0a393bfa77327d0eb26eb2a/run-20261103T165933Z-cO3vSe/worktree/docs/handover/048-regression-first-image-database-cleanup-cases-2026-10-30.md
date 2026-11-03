## Regression-first image/database cleanup cases (2026-10-30)

The user confirmed four ZIP restore cases passed locally in 33.49s and reported
a green workflow. No run ID/tested SHA/full suite counts were supplied for
independent verification. Those results do not cover the database-failure cases.

At the user's explicit request, this commit adds the known-failing regression
module before any runtime cleanup fix. python/tests/test_image_database_failures.py
contains upload/replacement crossed with failure before the database write, after
a real write and at the pre-commit driver boundary. Image storage really succeeds
and a real PNG is decoded before fault injection. SQL, transaction rollback,
authorized state/image reads and integrity checks use real SQLite/FastAPI paths;
a scoped proxy rejects the selected connection's commit before delegating it.
This is fault injection, not an actual exhausted disk or a post-commit ambiguity.

The user's Python 3.14 local run reported six failed, one warning in 16.38s.
Every case reached the intended boundary and passed exception/event checks,
unchanged database dump, integrity/foreign-key checks, absence of a row referencing
the failed path, unchanged viewer state/rendered image and no success publication.
All six then failed at the filesystem inventory comparison: one new PNG remained,
with the existing image identical. This establishes the orphan-artwork defect
for these six scenarios. Successful-retry sections after that assertion were not
reached and remain unvalidated. The TestClient deprecation warning is separate.

Earlier assistant checks only parsed the candidate and exercised a commit proxy
against a small real SQLite fixture. The assistant did not run these HTTP tests:
its execution workspace lacked the checkout/FastAPI and used Python 3.12.8.
Do not substitute those preparation checks for the user-supplied HTTP result.

This is intentionally a red intermediate working-branch commit. Normal Python /
HTTP discovery collects the six failures; no xfail, skips, tolerance changes,
workflow exclusion or skip-ci marker hides them. Runtime upload/replace cleanup
is not changed here and must follow in a separate approved commit. It must cover
database context exit/commit, remove only the new owned image on failure, retain
the old referenced image, preserve the original error if cleanup itself fails,
and leave old-image deletion/cache notification after successful replacement.
These tests must subsequently pass through the retry sections as well.

README was reviewed and remains accurate for this test-only red baseline;
HANDOVER records the defect without claiming a fix. Application, shared fixtures,
requirements, workflow, collector, evidence and other branches are unchanged.
Focused command: python -m pytest -q python/tests/test_image_database_failures.py.
Remaining general crash/power-loss/unlink-failure/concurrency concerns and broader
application-test work are not resolved by this regression-first commit.


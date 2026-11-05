# Bugs 25/26: regression-first editor ordering checks

## Scope and decision

Target: dajomas/Looking-Glass, features/perplexity, 2026-11-05.
Bugs 25 and 26 are a coordinated work package with separately reviewable fixes.
Implement state-response ordering (25) before mask decode invalidation (26).
This step adds tests only; neither bug is fixed, accepted or closed here.

## Regression coverage

`python/tests/test_admin_editor_ordering.js` executes the complete current
`static/js/admin_map_editor.js` IIFE in a Node VM with controlled API promises,
image decodes, DOM doubles and polling callbacks. A test-only injected seam
observes state/mask identity and directly applies state for isolated mask tests;
production files are not instrumented or modified.

Bug 25 cases cover pre-action delayed polls, completion during a pending action,
overlapping polls (allowing either serialization or guarded concurrency), equal
revision incarnation replacement, late old-incarnation responses, and normal
external-DM fog/wall convergence. Action cases use the actual Undo UI callback.
Tokens intentionally move from incarnation-z to incarnation-a: random tokens
identify incarnations and must not be ordered lexicographically.

Bug 26 cases cover installed A -> pending B -> cached A, obsolete decode failure,
newer C winning over a late B success, and visible current decode failure.
Assertions inspect mask identity, arrow image URL and fog drawing where relevant.

## Validation and limits

Tests were authored and reviewed, not executed. No red-baseline counts, passing
results, CI success, browser validation or functional acceptance are claimed.
Run from the repository root:

```bash
node --test python/tests/test_admin_editor_ordering.js
```

The existing JavaScript CI job discovers top-level test_*.js scripts according
to README.md. This regression-first commit may make that job red until production
fixes land. First confirm that failures identify the intended races rather than
fixture defects; repair fixture defects before using results as evidence.

These are controlled JavaScript tests, not real browser/HTTP integration tests.
They do not validate server-side rejection of stale ordinary coordinate actions,
real image decoding, pixel correctness, every editor mutation route or arbitrary
multi-client scheduling. The direct-install mask tests deliberately isolate the
loader race even after state-order protection removes its documented trigger.

README.md was read and needs no change: runtime behavior and documented test
commands remain unchanged. HANDOVER.md links this focused record. Existing
historical audit findings and bug status records are unchanged. No migrations,
production changes, archive-only Patch material or unrelated cleanup are included.

## Unfinished work

Execute and review the baseline; implement bug 25 with incarnation-aware request
ordering across GET/action installation and preserve legitimate external changes.
Then implement bug 26 invalidation even on cache hits, identity checks before
installing either overlay, and suppression of obsolete decode errors while keeping
current failures actionable. Re-run focused and existing JavaScript regressions,
review appropriate browser coverage, and record actual evidence before acceptance.

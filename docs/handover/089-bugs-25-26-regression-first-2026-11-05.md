# Bugs 25/26: regression-first editor ordering checks

## Scope and decision

Target: dajomas/Looking-Glass, features/perplexity, 2026-11-05.
Bugs 25 and 26 are a coordinated work package with separately reviewable fixes.
Implement state-response ordering (25) before mask decode invalidation (26).
The initial step added tests only; neither bug was fixed, accepted or closed.
The subsequent bug 25 candidate and evidence are recorded below. Both bugs
remain open pending validation and acceptance.

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

## Initial validation and limits

Tests were initially authored and reviewed, not executed. No red-baseline counts,
passing results, CI success, browser validation or functional acceptance were
claimed in the initial regression-only delivery.
Run from the repository root:

```bash
node --test python/tests/test_admin_editor_ordering.js
```

The existing JavaScript CI job discovers top-level test_*.js scripts according
to README.md. This regression-first work may make that job red until production
fixes land. First confirm that failures identify the intended races rather than
fixture defects; repair fixture defects before using results as evidence.

These are controlled JavaScript tests, not real browser/HTTP integration tests.
They do not validate server-side rejection of stale ordinary coordinate actions,
real image decoding, pixel correctness, every editor mutation route or arbitrary
multi-client scheduling. The direct-install mask tests deliberately isolate the
loader race even after state-order protection removes its documented trigger.

README.md was read and needed no change for the initial tests-only step.
HANDOVER.md links this focused record. Existing historical audit findings and bug
status records are unchanged. No migrations, archive-only Patch material or
unrelated cleanup are included.

## Bug 25 implementation candidate (2026-11-05)

The user ran the focused tests after regression-first commit
`6e84c4fca37d62abfdacd872af5bbe65a32866bc` and supplied 3 passing / 7 failing
results. Failures were five bug 25 ordering/incarnation assertions and two bug 26
mask assertions, not fixture startup errors. The ordinary external-change,
newer-C-mask and current-mask-error controls passed.

`static/js/admin_map_editor.js` now centralizes all of its map-state GET success
installation in `readState`. Each read captures an incrementing generation;
only the current generation may update state or live controls. Starting a `run`
action fences older reads, even when that action ultimately fails or cancels.
Installing action/read state also fences outstanding reads. Polling does not
start while busy. Poll comparisons include cache_token identity even if fog and
wall versions are equal; tokens are never lexicographically ordered. Error
recovery, active-map refresh, transition-save refresh and startup/retry reads
share the guarded path. Background poll failures remain ignored as before.

No mask loading behavior is changed in this candidate. The two bug 26 regressions
remain intentionally red for its separate implementation. The existing regression
test file is unchanged.

### Executed sandbox validation

Node.js v20.20.1 was available in the assistant sandbox. The production source was
reconstructed from the live tool result and verified against Git blob SHA
`a90fbe2283870c4278de63c8206f7767a5c044ab` before editing. The existing focused
test script was reconstructed from the approved regression-first contents.
These runs used a minimal temporary repository layout, not a complete checkout.

- Original source, complete focused script: 10 tests, 3 pass, 7 fail, no skips.
  This reproduced the user's baseline.
- Candidate source, same complete script: 10 tests, 8 pass, 2 fail, no skips.
  Only bug 26 cached-A/late-B installation and obsolete decode error cases failed.
- Candidate with `--test-name-pattern='bug 25'`: 6 pass, 0 fail, 4 deliberately
  filtered/skipped bug 26 cases. This is not a full-suite no-skip validation.
- Candidate `node --check` via standard input: exit 0.
- Source byte size: 25,387 -> 25,290 (97-byte decrease). The greater-than-25,000
  growth rule is not triggered because this file decreases in size; no split or
  unrelated formatting changes were made. Other changed content is below 25,000.

No CI, full JavaScript/Python suite, HTTP integration, live server or browser
checks were run. The sandbox Node version is not CI's documented Node 24.
No bug closure or broad race-freedom is claimed. A newer-issued request invalidates
an older one even if the newer request fails; convergence then waits for a later
successful refresh. Ordinary coordinate actions still lack server-side stale
context protection; this client change is not a substitute for that separate work.

README.md and HANDOVER.md were reviewed again. They remain unchanged: no setup,
command or control changed, and the existing Current work link correctly points
to this record with fixes still pending acceptance. The implementation and this
updated existing handover record belong in the same proposed commit.

## Unfinished work

Obtain approval and deliver the bug 25 candidate, then validate it in the user's
checkout/CI. Implement bug 26 invalidation even on cache hits, identity checks
before installing either overlay, and suppression of obsolete decode errors while
keeping current failures actionable. Re-run focused and existing JavaScript
regressions, review appropriate browser coverage, and record actual evidence
before acceptance. Both bugs remain open.

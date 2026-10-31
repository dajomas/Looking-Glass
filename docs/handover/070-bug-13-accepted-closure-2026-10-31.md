# Bug 13: accepted closure and evidence limits (2026-10-31)

Closure baseline: dajomas/Looking-Glass, features/perplexity,
afb4ed2520dff205f9f2debdef99668a61db5079, verified as the live branch tip.

## Acceptance and authority

The user explicitly instructed Proceed with closing Bug 13 on 2026-10-31 at
01:17 CET, after delivery of the raw route-ID navigation correction. Record
Bug 13 as accepted and closed by that instruction. This current-status record
supersedes earlier pending/unaccepted statements in record 068 and its index
label without rewriting their historical evidence. Bug 2 remains closed.

User acceptance is separate from execution evidence. No successful post-correction
normal-checkout run, exact-corrected-SHA CI run or final manual Back to map result
was supplied in this conversation before closure. Do not infer that these ran,
passed, or were explicitly waived. Retain them as outstanding validation/evidence
items, not an invented all-green result for the closure baseline.

## Delivered scope

Original-image dimension changes are rejected while alternate artwork exists,
even when no double-reveal rooms are enabled. The existing write transaction,
current-map authorization and upload cleanup protect saved artwork/configuration
and play state. Same-size original replacement remains supported. Without
alternate artwork, dimension changes remain supported and can require wall
recalibration. The originally alleged rendering crash was not established.

Authorized admin HTML 400 responses for original-image replacement offer Back
to map at the same map's fog editor. The helper parses raw string route IDs,
rechecks map-management permission and emits a canonical fixed local URL.
Malformed/nonpositive/out-of-range IDs are rejected. JSON error envelopes and
unrelated error navigation are unchanged. This does not promise camera/draft
restoration, automatic geometry reconfiguration or repair of existing incompatible
artwork. General retirement/unlink/crash concerns and Bugs 14/15 remain separate.

## Delivery and evidence chronology

- 500ada998a34785a61f2cf4c87f74cdbed6f1ae9: original regression coverage.
- c70d2cb7ec06e41193d04a50e5902d272e789769: original compatibility guard.
  User-reported focused execution: 34 passed in 22.09 seconds. Reviewed run
  41144347353 explicitly passed all 11 original Bug 13 HTTP cases, but the run
  failed three deployment-document assertions; it was not an all-green run.
- Reviewed run 41145631726, attempt 1, tested
  b07df241f51556f61d8bf66f0dbe124a9621d3b6. All five jobs succeeded:
  Python/HTTP 1264 passed plus 29 subtests, JavaScript 28 scripts, browser 172,
  live 18 and recovery 6 passed. This predates both navigation revisions.
- The user manually observed the expected 400 message for a 4760 x 3080 original
  with alternate artwork, then withheld acceptance because Back to start left
  the fog editor. Full manual state preservation/retry was not explicitly reported.
- 5cf39c788122ed93f7bc629276465a30ee9bd592: navigation change and eight cases.
  The user's focused run reported 2 failed, 40 passed in 27.52 seconds. Both
  failing HTTP cases stopped at the return-link assertion; subsequent state,
  editor-return and retry assertions were not reached. The integer-only helper
  incorrectly rejected the actual raw string route parameter.
- afb4ed2520dff205f9f2debdef99668a61db5079: parsing correction and 18 helper
  regressions. Isolated preparation used the exact AST-extracted helper, doubled
  application dependencies and fresh pytest subprocesses: baseline 4 failed/
  14 passed; candidate 18 passed. This is not HTTP/application integration proof.
  Existing failing HTTP assertions were preserved, not weakened or skipped.

## Remaining validation and preservation

In a normal checkout, execute the complete focused suite and record the actual
source SHA, counts and failures separately from acceptance:

```bash
PYTHONPATH=python python -m pytest -q python/tests/test_error_return_map_ids.py python/tests/test_image_replacement_error_navigation_web.py python/tests/test_original_image_compatibility_web.py python/tests/test_double_reveal_web.py python/tests/test_double_reveal.py python/tests/test_image_database_failures.py
```

Review exact-source CI evidence and manually follow Back to map from a rejected
replacement, checking existing state and a supported same-size retry. Neither
this procedure nor closure constitutes proof of execution. No tests, CI run,
browser session or deployment exercise was executed for this closure update.

README.md and HANDOVER.md were reviewed live. README's overview remains accurate;
no cosmetic edit is required. Close only the individual Bug 13 TODO section and
add one short HANDOVER.md pointer to this record. Preserve record 068, all split
manifests, Bug 2 history, code/tests, workflows and other backlog statuses.
No runtime change, archive, Patch/ material, merge or other-branch write.

# Bug 13: regression-first original-image compatibility (2026-10-31)

Baseline: dajomas/Looking-Glass, features/perplexity,
abf31b19836da12c679632ab4a125f08850b8553, verified from the live branch.
Bug 2 remains accepted/closed under record 066. Bug 13 is next in backlog order.

## Decision and staged delivery

Reject original-image dimension changes while a double_reveal_maps record exists,
even without enabled rooms. Preserve same-size replacement and dimension changes
without alternate artwork. Do not resize/delete existing artwork or reset play
state. Matching dimensions cannot establish alignment. The alleged rendering
crash was not established; this is a defensive compatibility fix.

This first proposed commit adds regression coverage and this index pointer only.
It deliberately leaves runtime unchanged. A separate exact-approved commit must
add the prepared guard and necessary current usage/backlog/documentation updates.
Do not interpret the first test commit as a delivered fix or close Bug 13.

The prepared runtime candidate changes only campaigns.py::replace_image: after
storage, use BEGIN IMMEDIATE inside the existing cleanup context, reload and
re-authorize the map, check alternate presence and dimensions, and raise
BadRequest (400) before replacement/reconciliation on mismatch. Existing rollback
and reference-aware new-file cleanup remain; old-image deletion, invalidation and
success publication stay after commit. This is proposed code, not branch state.

## Coverage and actual validation

python/tests/test_original_image_compatibility_web.py contains 11 intended cases:
six dimension mismatches (width, height, both; configured or artwork-only),
same-size success preserving configuration/history/custom notes/alternate bytes,
dimension-change success without alternate artwork, alternate artwork committed
at the image-storage seam, and two authorization/CSRF cases. Real existing
HTTP/SQLite/image fixtures compare DB/file/viewer state, notifications and retries.
The seam injection is not a concurrent-process stress test.

The complete campaigns.py baseline was reconstructed and matched live Git blob
cd259bd88d4df41eee7699ce867fe7aef8e7906e. The prepared runtime candidate and
new HTTP module compiled on Python 3.12.8. Compilation is not collection.
An isolated eight-scenario matrix used AST-extracted route functions (without
FastAPI decorators/annotations or the reconciliation import), real SQLite
transactions and Pillow PNGs, but minimal schema and doubled authorization,
image-service wrappers, repository writes, reconciliation, cache and notification.
Baseline: 5 passed, 3 failed (all mismatches with alternate artwork).
Prepared candidate: 8 passed. Rejection checked unchanged rows/file bytes and no
reconcile, invalidation or publication. This is not HTTP/full-schema evidence.
An initial notebook asyncio.run invocation failed before executing a case;
complete matrices subsequently ran in a worker thread.

FastAPI/Starlette are absent here. The 11 intended HTTP cases were not collected
or executed. They are expected to expose the missing guard on this test-only
baseline; no xfail, skip or workflow exclusion conceals them. No full application,
browser/live, CI, deployment or Python 3.14 pass is claimed. No user acceptance
of the fix is recorded. After the implementation commit, execute:

```bash
PYTHONPATH=python python -m pytest -q python/tests/test_original_image_compatibility_web.py python/tests/test_double_reveal_web.py python/tests/test_double_reveal.py python/tests/test_image_database_failures.py
```

Also verify actual CI SHA/run/attempt/results, broader application coverage and
visible UI rejection followed by successful same-size retry. Do not manufacture
acceptance from compilation, isolated checks or commit delivery.

## Documentation and remaining work

README.md and the current double-reveal usage section were reviewed. README's
overview remains accurate; no cosmetic edit is needed. Usage/backlog updates
belong with the runtime commit. HANDOVER.md receives only this short pointer.
Historical split manifests, Bug 2 records, dependencies, migrations, workflows,
other branches and archive-only Patch/ material are unchanged.

The follow-up must retain existing database-failure cleanup coverage and test
current-state rechecks before success. Existing incompatible installations,
image retirement/unlink failures, crashes and explicit dimension-changing
reconfiguration remain outside scope. Cleanup inherits existing conservative
retention if reference verification or deletion fails. Bugs 14/15 stay separate.

## Regression delivery and runtime follow-up

The regression-first commit succeeded as
500ada998a34785a61f2cf4c87f74cdbed6f1ae9 on features/perplexity. Post-write
reads verified test blob 95a0d297e2eafa26dfa456617230331f7c0d1d33 and unchanged
campaigns.py baseline cd259bd88d4df41eee7699ce867fe7aef8e7906e. No tests ran
during that write. The earlier proposed/unchanged-runtime statements above
describe that first stage, not the containing runtime follow-up.

This containing commit completes implementation delivery when its approved write
succeeds. It adds the nine-line compatibility guard described above, updates
the current usage section and marks the individual backlog item implementation
delivered, not accepted. Report the actual returned commit SHA only after success.
The runtime candidate is Git blob ac251388575d9e5c3d3a14c19ad48f222c1c6a94,
matching the earlier compiled and isolated-tested candidate. Tests are preserved
unchanged. This source identity check is not a fresh test execution.

The lock precedes map reload and alternate lookup, serializing the decision with
alternate uploads. Reauthorization and the current old-image path come from that
transaction. Rejection precedes note reconciliation and all successful-replacement
side effects. Only this route changes runtime behavior; upload, deletion, restore,
retirement and schema handling are not redesigned.

No application tests or CI evidence were executed/reviewed in this follow-up.
The normal-checkout command and UI/CI acceptance above remain outstanding.
README.md still needs no edit; HANDOVER.md already points here and needs no
additional index churn. Original split manifests stay untouched. An existing
incompatible alternate image is not repaired by this guard, and same-size
replacement cannot validate alignment. Do not deploy the isolated-test result
as proof of HTTP, concurrent-process or target-Python acceptance.

## Acceptance follow-up: return to the fog editor (2026-10-31)

Baseline for this navigation follow-up: features/perplexity
ad6e180c63c9a2163c523da2cbbad73fe2a5f141. The original guard was delivered
in c70d2cb7ec06e41193d04a50e5902d272e789769. The user reported 34 focused
passes in 22.09 seconds and later confirmed the actual 400 dimension message
for a 4760 x 3080 original with alternate artwork. An earlier 90%-size original
replacement without alternate artwork was supported behavior. The user explicitly
withheld closure because Back to start left the fog editor. Bug 13 is not accepted.

Reviewed retained CI run 41145631726, attempt 1, tested
b07df241f51556f61d8bf66f0dbe124a9621d3b6: all five jobs succeeded. Python/HTTP
1264 passed plus 29 subtests, JavaScript 28 scripts, browser 172, live 18 and
recovery 6 passed. Earlier run 41144347353 explicitly passed all 11 Bug 13 HTTP
cases but failed three deployment-doc tests, subsequently corrected. These
results supersede the historical HTTP/CI-pending preparation wording above for
the original guard, not for this new navigation change. Manual full-state
preservation and same-size retry were not explicitly reported by the user.

Change web/errors.py and templates/error.html only for runtime behavior. HTML
400 responses to authorized admin POST /maps/{map_id}/image offer Back to map
at /maps/{map_id}. Require a positive integer route parameter and the exact
replacement path, an authenticated request user without a forced password change,
and a fresh map-management permission check. Forbidden/missing maps fall back to
generic navigation. The target is a fixed local server-generated path: ignore
Referer, next and other client-supplied return URLs. JSON errors retain their
existing status/envelope and bypass link lookup. Other statuses/routes and both
portals' unrelated errors retain Back to start. The existing template fallback
also works when no return_map_url is supplied. This adds a read-only permission
lookup, not a new replacement write or a fog/viewer operation. Loading the editor
uses its existing authorization and ordinary read/reconciliation behavior; no
new activation or reset is introduced. No camera/draft restoration is promised.

Add test_image_replacement_error_navigation_web.py with six intended HTTP cases
and two helper permission-denial cases. Coverage checks configured/artwork-only
rejections, safe link selection despite malicious Referer/next, unchanged
DB/files/viewer output before and after following the editor link, no publication,
same-size retry, unchanged JSON envelope and generic 403/404 fallback. Unit access
denials cover Forbidden and NotFound. Existing compatibility tests remain unchanged.

Actual preparation: baseline errors.py and error.html matched their live Git
blobs. Candidate errors.py and the complete new test module compiled on Python
3.12. Eleven isolated checks executed the AST-extracted error helper functions
and actual candidate Jinja template with a synthetic base layout and doubled
requests, permissions, DB contexts and response/render wrappers. Baseline:
10 passed, 1 failed (authorized replacement still linked to /). Candidate:
11 passed. Checks included JSON/status isolation, viewer/GET/other-path fallback,
invalid ID, revoked/missing access, forced password change and HTML escaping.
This is not HTTP/application or full-template integration execution. FastAPI is
absent here, so none of the eight intended new pytest cases was collected or run.
No new CI or deployment result is claimed. Run in a normal checkout:

```bash
PYTHONPATH=python python -m pytest -q python/tests/test_image_replacement_error_navigation_web.py python/tests/test_original_image_compatibility_web.py python/tests/test_double_reveal_web.py python/tests/test_double_reveal.py python/tests/test_image_database_failures.py
```

Then review the exact delivered-SHA CI run and manually follow Back to map from
the rejection. Bug 13 remains pending acceptance, not closed by this follow-up.
README.md and HANDOVER.md were reviewed live; README's overview is unchanged and
the existing short HANDOVER.md pointer already leads to this focused record.
No cosmetic documentation/index edit, historical manifest change, schema,
dependency, workflow, other-branch write or archive-only Patch/ material is needed.

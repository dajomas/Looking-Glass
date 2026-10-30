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

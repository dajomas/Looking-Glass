# Bug 14: accepted closure and evidence limits (2026-10-31)

Repository: dajomas/Looking-Glass. Working branch: features/perplexity.
Preparation baseline: 130a3b25f4aa1ef2507258a1111fdd0eb2a16dbf,
verified as the live branch tip on 2026-10-31. This is not an assertion of the
exact source SHA used in the user's manual execution.

## Acceptance and authority

At 15:44 CET on 2026-10-31, the user instructed: Yes, close Bug 14 and check the
next bug. Bug 14 is accepted and closed by that instruction. Bugs 2 and 13 remain
accepted and closed. Historical open/pending/red-baseline statements do not
supersede this current acceptance. Bug 15 remains separate and open.

Immediately beforehand, the user reported executing the manual test plan and
that the current implementation worked according to its expected results.
Record this as user-reported manual acceptance, not assistant-executed testing.
The user did not supply the exact manually tested current SHA, raw inventories,
screenshots, logs or a separate old-baseline reproduction outcome. Do not infer
those details or block the explicitly requested closure on their absence.

## Delivered implementation and manual scope

Cleanup was already delivered in
87850207839691354af438551f3736e41d113f38. campaigns.py uses
_image_write_connection for uploads and original-image replacement, enclosing
database context exit/commit. After exceptional exit it checks a fresh database
connection for a committed maps.image_file reference, removes only an unreferenced
new owned image, and preserves the original error if ordinary verification or
cleanup fails. Referenced images or unverifiable cleanup are conservatively
retained. This closure introduces no runtime fix.

The manual plan covered valid image upload without walls; oversized accompanying
walls rejected without a failed map row or new PNG; preservation of existing
control artwork; successful retry retaining its own image; and small malformed
walls preserving map-import partial success with a wall warning. It combined
browser actions with read-only database/file inventories. The proposed old-code
comparison used 3d34a4f8d2c5f184d5e667aa4e47de2a22ee3c10 and fresh isolated data;
the report establishes the current expected results, not an independently
reported outcome for that old baseline.

## Existing evidence and limits

Record 048 preserves the older deliberately red six-case database-failure
baseline. Its failures are historical, not a current failure claim. The live
python/tests/test_image_database_failures.py retains upload/replacement crossed
with before-write, after-write and pre-commit driver-boundary injections, real
HTTP/SQLite/image checks, unchanged prior state/files/viewer output, no success
publication and subsequent retries. test_import_policy_routes.py additionally
contains isolated route/helper checks, including oversized walls, partial
success, reference retention and cleanup-error preservation. Isolated doubles
are not real HTTP/rollback execution.

The user previously reported a focused run containing the database-failure
module with 34 passes in 22.09 seconds; this is an aggregate suite result, not
34 cases in that module. Record 070 records reviewed integration run 41145631726,
attempt 1, green across all five jobs against
b07df241f51556f61d8bf66f0dbe124a9621d3b6. That evidence predates Bug 13 navigation
follow-ups and is not exact-current-tip proof.

No compilation, pytest, application/HTTP/browser execution or new CI review was
performed for this closure. Manual acceptance does not establish deterministic
cancellation behavior during worker-backed image storage, commit-time campaign
permission-race behavior, process-crash/power-loss safety, guaranteed unlink
success or new injected database-failure results. Retain these limits without
turning them into instructions to reopen accepted Bug 14. Bug 13's final
corrected-SHA validation limits remain unchanged.

## Documentation and next work

README.md and HANDOVER.md were reviewed live. README remains accurate and needs
no cosmetic edit. Update the individual Bug 14 TODO and add one short pointer in
HANDOVER.md. Preserve historical records and split manifests. No runtime, tests,
workflow, migration, dependency, archive, Patch/ material or other-branch change.

The next unresolved backlog item is Bug 15, deletion/restore leaks of alternate
image files, as recorded in docs/todo/016-bug-15-deletion-restore-leaks-alternate-image-files.md.
Initial source review finds campaigns.py deletion and successful restore cleanup
using original maps.image_file paths only. double_reveal.py upload_image retains
replaced alternate files deliberately for in-flight render and backup readers.
Its artwork endpoint also returns path-based FileResponse values after the DB
read transaction ends. These are source observations, not a newly executed
reproduction or an approved retirement design. Do not solve the leak by blindly
unlinking old alternate paths or scanning/deleting arbitrary untracked files.
Investigate reader lifetime, transactional path collection, reference-checked
retirement and regression coverage before proposing Bug 15 runtime writes.

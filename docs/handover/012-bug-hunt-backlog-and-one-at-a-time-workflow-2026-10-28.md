## Bug-hunt backlog and one-at-a-time workflow (2026-10-28)

The user superseded the combined-fix approach: keep the 15 findings and proposed
solutions in root TODO.md and tackle them individually. All 15 entries are open;
this documentation change does not deliver fixes, tests, migrations or assets.
The live branch was observed at 3d34a4f8d2c5f184d5e667aa4e47de2a22ee3c10 before
preparing this backlog. No earlier combined implementation was committed.

Treat earlier replacement snippets, local candidate files and candidate test
results as uncommitted exploratory work, not branch state. Re-read live source,
reproduce each issue, agree a minimal compatible solution, add regression tests,
record actual results, update relevant docs and obtain exact-write approval for
each delivered change. Never apply the earlier combined draft wholesale.

TODO.md preserves audit corrections: imported-name release is intentional and
must remain lossless for custom notes; the originally alleged double-reveal
rendering crash was not established. Archive/recovery models and retirement
queues are design proposals, not an installed or approved migration 18.

The uploaded base64 source ZIP names the audit revision and matched checked blob
hashes, including README.md and this handover. Prefer future live branch state.
No application tests were run for this documentation-only backlog change. Prior
candidate testing does not validate the unchanged implementation on the branch.
A pre-existing scrying-auto-2 template assertion failure was reproduced on the
untouched baseline; keep it separate from these 15 items.


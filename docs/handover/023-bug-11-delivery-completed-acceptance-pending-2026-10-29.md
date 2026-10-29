## Bug 11 delivery completed; acceptance pending (2026-10-29)

All four approved delivery steps are committed to features/perplexity:
1. HANDOVER preparation: df9ad36b369b77aa2e896dd56dff95fb45d6fb7c.
2. Importer, numeric/parser tests and import guide: f03520b8ac76a2155a3af3eef4fc0c878acb71b6.
3. Apply/saved-source routes: 0f537c9b5b2e4881997da3ccb18e05543009b5f3.
4. Direct inspection and route-body tests: c21c0d1a299449eadf93ec8188afe6caf799654d.
TODO completion is committed in a024f61ac94126375831cae9b092fcd0e9959d86.
Historical candidate/open wording above describes preparation, not current delivery.

A fresh focused run immediately before step 4 approval passed all 202 cases,
none failed or skipped, in 0.26 seconds on Python 3.12.8: 154 numeric/parser,
16 isolated route-body, eight existing importer and 24 NeDB replay cases.
All six complete candidate Python files compiled successfully. The delivered
files are the exact tested candidates; no paired-dimension restriction was added.
No tests were rerun after the GitHub writes or for this documentation-only update.

The focused package used empty initializers and a minimal conftest with the
existing scene helper; unchanged support/test files matched live Git blobs.
Parser/calibration logic is real. Route tests load actual function bodies from
complete modules through AST, removing decorators and annotations; DB/repository,
permission, request/response, fog and reconciliation boundaries are doubles.
These checks prove isolated ordering, not persistent-DB rollback or HTTP acceptance.

Integration/deployment acceptance remains unfinished: run the four-module focused
command above in a normal checkout, add and execute real HTTP/DB inspection,
import and saved-source cases, and verify unchanged stored geometry on rejection
for automatic and retained calibration. Full application imports/registration,
authentication/CSRF, migrated DB, full suite, extended portal graphs, browser,
live-server and Python 3.14 acceptance were not executed. Retain the ZIP skip,
legacy-data and upload/file-lifecycle limitations documented above.

Five backlog implementations remain open: 12, 2, 13, 14, 15, in that suggested
order. Delivered implementations and pending acceptance are separate statuses.
README remains unchanged; this update adds no runtime code, tests or Patch/ material.


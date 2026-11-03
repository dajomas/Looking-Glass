# Second bug hunt: bugs 16–29

Date: 2026-10-31. Reviewed repository `dajomas/Looking-Glass`, working branch
`features/perplexity`, baseline `766780262bf44922bbd7c9fa2b3081e7e28e214f`.
The branch still resolved to this SHA at the final pre-approval read.

## Decisions and scope

Documentation-only review: no implementation, migrations, test changes, bug
closures, merges or archives. TODO.md remains an index; bugs 16–29 link to
numbered sections in [the focused audit](../todo/018-bugs-16-29-audit-2026-10-31.md).
Each includes source locations, impact, a proposed reproduction, minimal fix
approach and required regression. Preserve accepted status/evidence for bugs
1–15; do not infer current counts from the historical workflow section.
Original-image replacement findings 17/18 do not reopen bug 15's accepted scope.

Proposed order: 16, 17, 18, 19, 20, 21, 23, 29, 25, 26, 27, 28, 22, 24.
Coordinate original-image retirement 17/18 and state/mask sequencing 25/26.
README.md was read and needs no change for this backlog-only review; no new
implemented behavior is being advertised. Historical split manifests remain
unchanged. HANDOVER.md receives only this navigation link.

## Validation and unfinished work

Three extracted sandbox checks ran: copied CalibrationIn declarations under
Pydantic 2.11.4 accept an infinite offset and SQLite retains it; Node accepts
the slash/backslash redirect predicate and resolves it externally; Node shows
the poll inequality installing old fog version 8 over current version 10.
These are isolated behavioral checks, not repository regression tests.
All application-level reproductions and proposed regressions remain pending.
No application, HTTP, browser, live-server, full-suite or CI run was executed.
The source review was selective, not exhaustive. All 14 new findings stay open.

Database triggers were checked before recording findings: hide_all does reset
runtime door/passage states, and double-reveal writes do bump fog_version;
those apparent issues were excluded. Future fixes must inspect current branch
code, agree scope, reproduce, add regressions, implement and validate, then
obtain approval for the exact GitHub write. This record documents the proposed
review content, not an assertion that the pending commit already succeeded.

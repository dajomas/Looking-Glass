# Bug-fix TODO

Created: 2026-10-28. Audited baseline: `3d34a4f8d2c5f184d5e667aa4e47de2a22ee3c10`.
Target: `dajomas/Looking-Glass`, branch `features/perplexity`.

## Workflow

Bugs 1, 3, 4, 5, 6, 7, 8, 9, 10, 11 and 12 have delivered implementations; the other 4 items remain open.
Bugs 4, 5, 6, 7, 8, 9, 10, 11 and 12 integration/deployment acceptance remains pending; see their validation limits below.
The earlier combined draft was not committed; do not apply it wholesale.
Re-read live code and reproduce each remaining finding before fixing.
For each item: agree a minimal solution, add a regression, implement, validate,
update relevant docs and HANDOVER.md, then approve the exact GitHub write.
Check off only after delivery; record commit SHA, actual test results and limits.
Proposed solutions/migrations are not installed or pre-approved changes.

Suggested remaining order: 2, 13, 14, 15.
Coordinate session items 5-7, parser items 10-12 and image-lifetime items 4/14/15,
while keeping changes individually reviewable. Package paths below refer to
`python/looking_glass/`; static findings still need application-level reproduction.

## Findings and proposed solutions


### 15. Deletion/restore leaks alternate-image files
- [x] Accepted and closed on 2026-10-31 by explicit user instruction at 22:10 CET,
  after confirming the two observed container errors were missing-Docker setup
  failures rather than Bug 15 execution failures.
- Delivered/tested implementation: 000c46030807ab55b89e47a0f9e4f08da9dcb4de.
  Known old original/alternate paths are transactionally retired for deletion,
  restore and alternate replacement; normal POSIX CLI ownership protects readers
  from explicit offline collection. No arbitrary old untracked-file scan.
- User-executed focused run: 77 passed in 31.72s. Full Python/HTTP: 1327 passed
  plus 29 subtests in 156.86s. The broader log shows all 37 new retirement cases
  passed, browser 172 passed and live 18 passed. Counts overlap, not additive.
- Retain two container setup errors, outstanding container assertions, incomplete
  diagnostic packaging and unreviewed exact-source all-green CI as evidence
  limits, not invented passes or automatic instructions to reopen this closure.
- Original replacement/failed-new-file contracts, existing tests and CI remain
  unchanged. Stop/coordinate direct and older readers before collection; local
  POSIX/single-serving-process model only.
- Current authority: [accepted closure and evidence](../handover/074-bug-15-accepted-closure-2026-10-31.md).
  [Implementation history](../handover/073-bug-15-route-cli-integration-2026-10-31.md);
  [offline maintenance](../image-retirement.md).

### 14. Failed map uploads leave orphan artwork
- [x] Accepted and closed by explicit user instruction on 2026-10-31 at 15:44 CET.
- Delivered cleanup: 87850207839691354af438551f3736e41d113f38 adds reference-aware
  new-image cleanup around upload/replacement database context exit and commit.
- User reported that the current implementation met the expected results of the
  manual test plan: valid import, oversized accompanying-wall rejection without
  orphan artwork, preserved control image, successful retry and intentional
  partial success for small malformed walls. Exact manually tested SHA and
  separate old-baseline reproduction results were not supplied.
- Closure is user acceptance, not proof of new assistant execution, exact-tip CI,
  cancellation safety or commit-time permission-race coverage. Preserve existing
  regressions and their evidence limits; do not reopen this item from historical
  red-baseline statements.
- See [accepted closure and evidence limits](../handover/071-bug-14-accepted-closure-2026-10-31.md).
- Alternate-image deletion/restore/retirement remains separate under Bug 15.

### 9. Login throttle retains unlimited keys
- [x] Implementation delivered on `features/perplexity`; HTTP/deployment acceptance pending.
- Fix commit: `a0610c6b6a7af13b7b516a992364b4a38035ccd6`.
- README commit: `dcd93fcee0d62508c541a13042e5874f5f50e28d`.
- HANDOVER commit: `d91cd4d9651319464f66ffa22db02c5c607d648b`.
- Baseline: `978a16333d40137045b0480931cab45d8709da88`. The user separately
  approved fail-closed capacity handling and documentation-first, three-commit
  delivery for bug 9 only.
- Validation during preparation on Python 3.12.8 using stdlib unittest:
  baseline produced 15 failures and 2 passes; candidate passed all 17 tests,
  none skipped. Both changed/new Python files compiled. A separate probe with
  4,200 distinct failure keys retained exactly 4,096 keys/timestamps and blocked
  an overflow key. Tests used the complete real security module in a temporary
  focused package with an empty initializer and a deterministic monotonic clock;
  real threads exercised concurrency. This was not HTTP/application execution.
  No pytest/project-conftest, full-suite, browser, live-server, multi-process or
  Python 3.14 deployment acceptance ran. No tests were rerun during GitHub delivery
  or this TODO-only update. See HANDOVER.md for commands and measured scope.
- Problem: checks allocated empty entries, failure histories grew without a bound,
  and expired abandoned keys were never reclaimed globally.
- Solution: checks no longer allocate; checks/failures prune expired histories
  under the existing lock. Retain at most 4,096 keys and the newest configured
  failure-threshold timestamps per key. At capacity deny untracked keys rather
  than evicting active histories. Preserve rolling-window expiry, case handling,
  successful reset and existing nonpositive-setting admission behavior.
- Test: allocation, expiry boundaries, newest-history bounds, abandoned-key cleanup,
  saturation without eviction, reset/expiry recovery, IP/case isolation, concurrent
  operations, nonpositive settings, an in-flight capacity race and 1,000 seeded
  reference-model operations below capacity.
- Limits: saturation can deny legitimate new-key logins; checks do not reserve
  slots or cancel in-flight authentication. A new-key failure finishing at capacity
  is not retained, and later checks see saturation. State remains process-local;
  cleanup is request-driven and scans the bounded table under its lock. Bounds
  cover entry/timestamp counts, not arbitrary key bytes or deployment-wide traffic.
  No schema, dependency, configuration key or route change was introduced.
- Remaining acceptance: run the regression module with normal dependencies and
  verify failure/429/reset behavior and capacity recovery on both portals and the
  Python 3.14 deployment before declaring HTTP/deployment acceptance complete.


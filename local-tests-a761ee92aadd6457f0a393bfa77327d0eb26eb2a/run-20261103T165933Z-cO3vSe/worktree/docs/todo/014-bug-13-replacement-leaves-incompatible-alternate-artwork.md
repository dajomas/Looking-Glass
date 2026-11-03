### 13. Replacement leaves incompatible alternate artwork
- [x] Closed by explicit user acceptance on 2026-10-31 at 01:17 CET.
  Closure includes the Back to map navigation follow-up and raw route-ID correction.
  Acceptance is not a new test result or blanket deployment approval.
- Problem: original-image dimension changes could leave alternate artwork and
  configuration incompatible. The originally alleged rendering crash was not
  established: dimension changes also invalidate room geometry keys.
- Delivered: reject dimension changes while an alternate-artwork record exists,
  even without enabled rooms; preserve same-size replacement and dimension changes
  without alternate artwork. Check current authorized map state under the write
  lock and retain failed-upload cleanup. HTML replacement errors offer a fixed,
  authorized Back to map link; raw route strings are parsed before permission checks.
- Evidence: user-reported original focused suite 34 passed in 22.09 seconds;
  reviewed CI 41145631726 attempt 1 passed all five jobs at
  b07df241f51556f61d8bf66f0dbe124a9621d3b6, before navigation changes.
  Navigation revision 5cf39c788122ed93f7bc629276465a30ee9bd592 then had a
  user-reported 2 failed/40 passed run. Correction
  afb4ed2520dff205f9f2debdef99668a61db5079 passed 18 isolated helper cases,
  not a normal-checkout HTTP run. Its full focused rerun, exact-SHA CI and final
  manual navigation check remain unreported; do not infer passes from acceptance.
- Current status and evidence limits:
  [Accepted closure](../handover/070-bug-13-accepted-closure-2026-10-31.md).
- Historical implementation and validation:
  [Bug 13 record](../handover/068-bug-13-original-image-compatibility-2026-10-31.md).


### 13. Replacement leaves incompatible alternate artwork
- [x] Implementation delivered by this containing commit; HTTP/CI, deployment and
  user acceptance remain pending. The checkbox does not mean accepted closure.
  The originally alleged rendering crash was not established: dimension changes
  also invalidate room geometry keys.
- Problem: original-image dimension changes leave alternate artwork/configuration stale.
- Solution: reject dimension changes while an alternate-artwork record exists,
  including when no rooms are enabled; retain same-size replacement and dimension
  changes without alternate artwork. Never silently discard artwork or play state.
  Recheck current authorized map state under the replacement write lock and use
  existing failed-upload cleanup.
- Regression coverage: 11 intended HTTP cases delivered in
  500ada998a34785a61f2cf4c87f74cdbed6f1ae9; compiled, not executed here.
  Earlier isolated extracted-route matrix: baseline 5 passed/3 failed; candidate
  8 passed. These are not HTTP/application or CI acceptance results.
- Acceptance: verify rejection preserves DB/original/alternate/configuration/notes/
  fog and viewer output, removes the failed upload and emits no success event;
  same-size retry and dimension changes without alternate artwork remain supported.
- Details and remaining validation:
  [Bug 13 record](../handover/068-bug-13-original-image-compatibility-2026-10-31.md).


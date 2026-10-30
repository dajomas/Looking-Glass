### 13. Replacement leaves incompatible alternate artwork
- [ ] Open; defensive compatibility fix. The originally alleged rendering crash
  was not established: dimension changes also invalidate room geometry keys.
- Problem: original-image dimension changes leave alternate artwork/configuration stale.
- Solution: reject dimension changes while alternate artwork exists, or agree
  explicit reconfiguration; never silently discard artwork or play state.
- Test: rejection preserves DB/original/alternate state and removes failed uploads;
  same-size replacement remains supported.


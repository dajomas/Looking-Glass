### 15. Deletion/restore leaks alternate-image files
- [ ] Open; static lifecycle finding; coordinate with items 4 and 14.
- Problem: map/campaign deletion, replacement and restore remove alternate DB
  references but clean only originals; immediate deletion can break readers.
- Solution: collect both paths transactionally and use reference-checked retirement.
  Startup-only collection is an option, not CLI/context construction under a
  serving process. Never blindly delete existing untracked files.
- Test: both images are covered, rollback preserves files, and collection is
  idempotent/path-contained and respects active references and supported readers.


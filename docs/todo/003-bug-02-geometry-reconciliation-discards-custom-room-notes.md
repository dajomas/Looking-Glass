### 2. Geometry reconciliation discards custom room notes
- [ ] Open; data-retention risk. Imported-name release itself is intentional.
- Problem: `services/room_notes.py` reconciliation, including during admin reads,
  can delete custom names/Markdown when geometry changes.
- Solution: retain recoverable orphan/archive content while releasing assignments.
  Define read behavior and management-only, revision-safe recovery; preserve
  retained notes in backup/restore and duplication.
- Test: split/merge/alignment changes retain edits and map isolation, release
  names correctly, and allow recovery without changing fog.


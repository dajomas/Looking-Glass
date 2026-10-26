| Step             | Feature                             | Scope of the first implementation                                                                                                        |
| ---------------- | ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| 1 — suggestion 2 | Campaign readiness checks            | Read-only report with actionable links; no automatic repairs.                                                                            |
| 2 — suggestion 4 | Campaign-wide quick navigation       | Search maps, named areas, notes, and passage endpoints; navigation remains admin-only unless explicitly choosing a player-facing action. |
| 3 — suggestion 1 | Named session checkpoints            | Capture and restore campaign play state without replacing authored content.                                                              |
| 4 — suggestion 8 | Backup inspection and safer restore  | Preview archive contents and compatibility before replacement; add a recovery safeguard.                                                 |
| 5 — suggestion 3 | Viewer synchronization status        | Distinguish connected, loading, up to date, and failed/reconnecting viewers.                                                             |
| 6 — suggestion 6 | Clean map/campaign duplication       | Copy authored content, remap internal connections, and deliberately reset play state.                                                    |
| 7 - New bug | Give feedback while importing large files | When importing a large file (like a map), there is no feedback to the user. This might cause multiple clicks on the import button, causing more than one import to occur. Give feedback when importing any file so the user knows the system is busy. |


## Implementation progress

- Step 1: implemented — campaign readiness checks and read-only DM inspection.
  Service/template checks validated; HTTP and browser acceptance remain to be run in
  the development installation. See docs/usage.md and docs/testing.md.
- Step 2: implemented — campaign-wide quick navigation, including Ctrl/Command+K,
  filtered search and read-only DM result inspection. Service/template and DOM-stub
  regressions validated; HTTP and real-browser acceptance remain outstanding.
- Step 3: implemented — named campaign-wide session checkpoints, read-only restore
  preview, compatibility/freshness guards and transactional automatic safety checkpoint.
  Service/template and migration regressions validated; HTTP and browser acceptance remain
  outstanding in the development installation.
- Steps 4–6: pending; their scope and order above remain unchanged.
- Item 7 (file-import busy feedback): deferred until after the suggestions, as requested.

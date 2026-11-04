# Bug-fix TODO

The original backlog is preserved verbatim in the ordered files below.
Read workflow/scope before continuing a bug. This documentation-only split
changes no bug status, implementation, validation claim or acceptance requirement.
Historical phrases such as "this containing commit" keep their original context.
Uncommitted bug-2 candidates are not installed branch changes.

## Contents

- [Workflow and scope](docs/todo/001-workflow-and-scope.md)
- [1. Feathered fog exposes hidden artwork](docs/todo/002-bug-01-feathered-fog-exposes-hidden-artwork.md)
- [2. Geometry reconciliation discards custom room notes](docs/todo/003-bug-02-geometry-reconciliation-discards-custom-room-notes.md)
- [3. Viewer stays blank after a transient state error](docs/todo/004-bug-03-viewer-stays-blank-after-a-transient-state-error.md)
- [4. Cache cleanup races with image responses](docs/todo/005-bug-04-cache-cleanup-races-with-image-responses.md)
- [5. Viewer sockets outlive session expiry/logout](docs/todo/006-bug-05-viewer-sockets-outlive-session-expiry-logout.md)
- [6. Role changes leave viewer sockets connected](docs/todo/007-bug-06-role-changes-leave-viewer-sockets-connected.md)
- [7. Forced password change is bypassed by WebSockets](docs/todo/008-bug-07-forced-password-change-is-bypassed-by-websockets.md)
- [8. Failed account forms partially save display names](docs/todo/009-bug-08-failed-account-forms-partially-save-display-names.md)
- [9. Login throttle retains unlimited keys](docs/todo/010-bug-09-login-throttle-retains-unlimited-keys.md)
- [10. NeDB imports resurrect deleted walls/scenes](docs/todo/011-bug-10-nedb-imports-resurrect-deleted-walls-scenes.md)
- [11. Wall imports accept non-finite coordinates](docs/todo/012-bug-11-wall-imports-accept-non-finite-coordinates.md)
- [12. Malformed imports escape as unexpected exceptions](docs/todo/013-bug-12-malformed-imports-escape-as-unexpected-exceptions.md)
- [13. Replacement leaves incompatible alternate artwork](docs/todo/014-bug-13-replacement-leaves-incompatible-alternate-artwork.md)
- [14. Failed map uploads leave orphan artwork](docs/todo/015-bug-14-failed-map-uploads-leave-orphan-artwork.md)
- [15. Deletion/restore leaks alternate-image files](docs/todo/016-bug-15-deletion-restore-leaks-alternate-image-files.md)
- [Validation caveats](docs/todo/017-validation-caveats.md)

## Second bug hunt: bugs 16–29

Audited source: `766780262bf44922bbd7c9fa2b3081e7e28e214f` on
`features/perplexity`, 2026-10-31. Bugs 16, 19 and 23 are accepted and closed.
Other findings remain open.
The original workflow's counts and suggested order are historical; do not use
them to reopen accepted bugs 2/13/14/15. Existing individual status records and
accepted handovers remain authoritative. This audit changes no earlier status.

The focused [audit record](docs/todo/018-bugs-16-29-audit-2026-10-31.md)
contains evidence, reproduction procedures, proposed solutions and regression
requirements. It describes the audited commit and is not edited as fixes land;
the status below is authoritative. Its linked numbered sections extend the
existing bug numbering:

- [16. Manual calibration bypasses finite-number validation](docs/todo/018-bugs-16-29-audit-2026-10-31.md#16-manual-calibration-bypasses-finite-number-validation) — closed 2026-11-03; see [accepted closure](docs/handover/082-bug-16-closure-and-bug-23-config-2026-11-03.md#bug-16-accepted-and-closed)
- [17. Original-image replacement deletes files still in use](docs/todo/018-bugs-16-29-audit-2026-10-31.md#17-original-image-replacement-deletes-files-still-in-use)
- [18. Old-image unlink failure interrupts post-commit notification](docs/todo/018-bugs-16-29-audit-2026-10-31.md#18-old-image-unlink-failure-interrupts-post-commit-notification)
- [19. Superadmin self-reset leaves other sessions valid](docs/todo/018-bugs-16-29-audit-2026-10-31.md#19-superadmin-self-reset-leaves-other-sessions-valid) — closed 2026-11-03; see [accepted closure](docs/handover/079-bug-19-accepted-closure-2026-11-03.md)
- [20. Login next accepts a cross-origin backslash redirect](docs/todo/018-bugs-16-29-audit-2026-10-31.md#20-login-next-accepts-a-cross-origin-backslash-redirect)
- [21. Login lacks cross-site submission protection](docs/todo/018-bugs-16-29-audit-2026-10-31.md#21-login-lacks-cross-site-submission-protection)
- [22. Multipart CSRF token can cause an unhandled type error](docs/todo/018-bugs-16-29-audit-2026-10-31.md#22-multipart-csrf-token-can-cause-an-unhandled-type-error)
- [23. Explicit missing configuration silently falls back to defaults](docs/todo/018-bugs-16-29-audit-2026-10-31.md#23-explicit-missing-configuration-silently-falls-back-to-defaults) — closed 2026-11-04; see [accepted closure](docs/handover/082-bug-16-closure-and-bug-23-config-2026-11-03.md#bug-23-accepted-closure-2026-11-04)
- [24. Malformed configuration structures bypass loader validation](docs/todo/018-bugs-16-29-audit-2026-10-31.md#24-malformed-configuration-structures-bypass-loader-validation)
- [25. Delayed admin polling can roll editor state backwards](docs/todo/018-bugs-16-29-audit-2026-10-31.md#25-delayed-admin-polling-can-roll-editor-state-backwards)
- [26. Mask early return does not invalidate an in-flight different mask](docs/todo/018-bugs-16-29-audit-2026-10-31.md#26-mask-early-return-does-not-invalidate-an-in-flight-different-mask)
- [27. Notes-only changes do not refresh other editors](docs/todo/018-bugs-16-29-audit-2026-10-31.md#27-notes-only-changes-do-not-refresh-other-editors)
- [28. Out-of-map fog points are clamped into real rooms](docs/todo/018-bugs-16-29-audit-2026-10-31.md#28-out-of-map-fog-points-are-clamped-into-real-rooms)
- [29. Async image upload holds a SQLite write lock across await](docs/todo/018-bugs-16-29-audit-2026-10-31.md#29-async-image-upload-holds-a-sqlite-write-lock-across-await)

Suggested implementation order from the audit: **16 → 17 → 18 → 19 → 20 → 21 →
23 → 29 → 25 → 26 → 27 → 28 → 22 → 24** (16, 19 and 23 are closed).
Severity and dependency rationale are in the audit record.
Add regressions first and keep each fix separately reviewable.
Items 17/18 can share a coordinated image-retirement design; 25 precedes 26.
No application, HTTP, browser, live-server or full-suite tests were executed
for this audit. Three extracted checks are described with their exact limits.

## Preservation

[The manifest](docs/todo/manifest.json) records source commit/blob, byte counts,
SHA-256 hashes and file order. Concatenate its `files` entries in order to
reconstruct the exact original UTF-8 TODO.md, including its final newline.
This index is not part of that reconstruction. Paths in preserved prose retain
their repository-root context. Update external old TODO.md fragment links to
the corresponding section files.

Edit the individual section files for future updates. The manifest identifies
the split-time snapshot; later edits will no longer match its original hashes.
Git history retains that snapshot. See [handover](HANDOVER.md) for project context.

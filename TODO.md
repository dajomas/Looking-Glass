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

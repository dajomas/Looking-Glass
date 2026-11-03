## Deploying imported-room list unassignment

Apply the changed/new-file archive on top of source ff7d99d (which includes the
room-geometry release fix). Stop the application and back up its database first.
Extract at the repository root, restart the application and reload the editor.
CSS and library-manager script query versions are updated to avoid stale assets.
No database migration, new configuration key or dependency is needed.

Unassign clears saved room metadata immediately, including custom edits, but keeps
imports and leaves fog untouched. For rollback restore previous code; restoring
cleared metadata requires a pre-action database backup or manually reassigning the
original imported entry. Reassignment does not recover discarded custom edits.


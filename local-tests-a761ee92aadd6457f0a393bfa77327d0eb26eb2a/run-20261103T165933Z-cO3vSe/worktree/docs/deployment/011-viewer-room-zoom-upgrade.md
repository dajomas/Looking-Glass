## Viewer room-zoom upgrade

Apply the changed/new files to the supplied 1618eef source containing split arrow visibility and locked doors. Stop the application processes, back up code/data normally, extract at repository root and restart both processes so the new read-only endpoint is available. Reload viewer tabs to load the versioned zoom helper/display script. No database migration, new dependency or configuration setting is required; the existing schema remains unchanged.

Verify focus/toggle on two revealed rooms, hidden-area no-op, manual pan then refit, Fit/F overview, resize, live hide/reset while focused, map switching/blanking, and drag/pinch suppression. Admin arrow visibility, viewer arrow visibility, lock/unlock and fog operations should be unchanged. See [testing](testing.md) for validation guidance. Rollback is the prior code version; this patch does not alter database contents/schema.



## Admin-controlled viewer zoom upgrade

Apply this changed-file archive to the supplied 13d62ae source (viewer room zoom already installed). Stop both processes, back up normally, extract at repository root, restart both processes and reload BOTH admin and viewer browser tabs. This is important: older viewer scripts ignore the new camera event type. No database migration, new dependency or configuration key is required. No rolled-back Center/Fit preferences are added.

With a live viewer connected, double-click a revealed admin area in Reveal and Hide modes; verify room focus/overview in the viewer, no admin camera movement, and no fog action. Verify ordinary delayed singles, immediate right-click inverse mode, regular arrows, locked/unlocked double-clicks, viewer-local double-click/F, multi-viewer behavior, inactive-map rejection, hidden-area no-op, disconnected screens and stale map changes. See [testing](testing.md) for automated checks and environment requirements. Roll back to prior code; this increment does not change database schema/data.



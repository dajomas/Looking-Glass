## Passage modal and sidebar updates

The map-passage main-action footer and exclusive sidebar peers remain unchanged.
Inspect destination is admin-only and does not activate viewers or prompt for fog.

### Independent configuration and session saving

Restart both portals after installing the updated save handler so create/update
responses include saved_endpoint_id. Reload the admin page to load the versioned
controller and renamed controls. No migration, dependency, port or configuration
change is required. Verify configuration/session draft isolation in both directions,
new-endpoint creation followed by session update, repeated revision-safe saves,
failed-save retention, Close/Escape warnings and inspection without viewer changes.
Full-server/browser checks should be run in your installed environment; see
[testing](testing.md). Rollback restores matching previous code/assets; this increment
requires no database rollback. Previously saved configuration/session edits remain
real data changes and are not undone by rolling back the UI.



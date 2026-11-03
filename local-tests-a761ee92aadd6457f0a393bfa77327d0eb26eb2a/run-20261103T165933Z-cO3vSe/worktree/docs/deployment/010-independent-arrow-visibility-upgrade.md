## Independent arrow visibility upgrade

Apply this changed-file archive to the supplied d457b93 source containing the locked-door patch. Stop both application processes, back up SQLite/data, extract at repository root, restart normally and reload admin tabs for the versioned script. Startup applies migration 9, copying every map's existing shared preference to both screen flags. Existing colors, lock state and fog history are preserved. No dependencies/configuration keys or Center/Fit features are added.

Verify all four admin/viewer combinations, including exact viewer-image preview, admin arrow clicks and locked-arrow double-click behavior. Admin-only toggles should not refresh the viewer; changing viewer visibility must update active viewer images. A viewer browser reload is not needed for new JavaScript because viewer scripts are unchanged. Rollback requires previous code and matching database backup; no down-migration is included. See [map controls](map-controls.md) for visibility behavior and [testing](testing.md) for validation.



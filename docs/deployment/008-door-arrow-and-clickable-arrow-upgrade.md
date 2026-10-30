## Door-arrow and clickable-arrow upgrade

This cumulative patch supports baseline schema 4, the color-only arrow schema 5 and the toggle schema 6. Stop both processes and back up the database/data. Extract the repository-root-relative replacement files, restart normally and reload admin pages. Startup applies migrations 5 and 6 only if needed. Existing colors and enabled/disabled settings survive the upgrade. Clicking requires no new migration, dependencies or configuration keys. New versioned admin script URLs load the click helper before the map editor.

Verify a room-to-hidden-room arrow on both screens; click it on the admin screen while Hide mode is selected, confirm the opposite room is revealed and Undo restores the prior fog. Check drag/pinch behavior, disabled arrows, retained color and stale clicks. The viewer remains read-only. Render cache identities change automatically; manual cache cleanup is optional. For rollback restore matching previous code and database backup; no down-migration is supplied.



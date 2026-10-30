## At the table and deployment

Click bounded rooms to reveal/hide; use Undo, Reveal all, Reset, player preview
and Blank as needed. F fits, the wheel zooms and dragging pans. Always inspect
the exact player preview after geometry changes.

Stop the service and back up the data directory before installing. Restart to
apply migration 4, then hard-reload DM and viewer tabs. Migration 4 adds a separate
per-map wall-type settings table; it leaves migration 3, cache tokens, snapshots,
source uploads and any legacy disabled_wall_types column intact. See
[map controls](map-controls.md), [deployment](deployment.md) and [testing](testing.md)
for compatibility and validation guidance.


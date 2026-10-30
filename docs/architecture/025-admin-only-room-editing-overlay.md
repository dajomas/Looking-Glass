## Admin-only room editing overlay

room_edit_marker.js requests a separate room-edit-overlay image using the selected
anchor and geometry key, then places it over the stage's real fog canvas. A solid
amber edge and translucent interior distinguish editing without writing fog_ops,
changing versions/checkpoints, modifying masks, or notifying players. A viewport
status label provides an explicit editing indication. Exiting edit mode clears
both immediately; request generations prevent late responses from restoring a
cancelled marker. Map geometry changes invalidate/refetch with the original key;
changed room shape is rejected rather than highlighting the wrong area. No edit
state is shared with other admins or viewers, and this is not a room-edit lock.


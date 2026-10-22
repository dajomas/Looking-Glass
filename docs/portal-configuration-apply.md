# Portal configuration Apply and Close

Apply configuration to draft updates the wall-editor draft and stays open. It is
not a database save. After applying, you can select another portal section, adjust
roles/states/routes, inspect the overview and apply again in the same popup.

- A changed Apply is one Undo/Redo operation, including paired target changes.
- An unchanged Apply creates no new undo step or pair ID.
- Each successful Apply refreshes the popup baseline, preventing stale-draft errors
  caused by its own previous Apply.
- Current section, popup position and scroll are preserved.
- The popup's live status region reports applied/pending/incomplete changes.
- Close closes the popup without applying newer changes. Cancel pending edits and
  Escape have the same discard scope: only edits since the last successful Apply.
  Earlier Applies remain in the main draft.
- After closing, Save wall set persists the draft. Main-editor Undo can undo
  changed Applies individually.
- Stale/invalid actions stay open with an error. Incomplete sections may be staged
  with Apply, but the existing Save/Download preflight still rejects unfinished
  graphs. No permission, viewer, fog or runtime behavior changes.

If you accidentally close after making newer edits, changes made after the last
Apply are discarded. Already applied changes are still present in the draft.
The separate wall-coordinate Edit dialog is not affected by this change.

See [deployment](deployment.md) for upgrade and rollback guidance, and
[testing](testing.md) for validation in the installed environment.

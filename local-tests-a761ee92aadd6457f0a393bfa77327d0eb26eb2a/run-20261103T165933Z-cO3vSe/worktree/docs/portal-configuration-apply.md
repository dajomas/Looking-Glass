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
- Close is the only close action; the duplicate Cancel pending edits button is removed.
  Close and Escape close immediately when the popup is clean. If unapplied edits
  exist, they ask before discarding them. Declining keeps the popup and edits open.
  Confirmed discard affects only edits since the last successful Apply; earlier
  Applies remain in the main wall draft.
- After closing, Save wall set persists the draft. Main-editor Undo can undo
  changed Applies individually.
- Stale/invalid actions stay open with an error. Incomplete sections may be staged
  with Apply, but the existing Save/Download preflight still rejects unfinished
  graphs. No permission, viewer, fog or runtime behavior changes.

Reset pairing… names the selected/paired sections affected and asks for confirmation.
It changes only this popup until Apply, keeps wall geometry and Portal type, and
can still be discarded with Close/Escape confirmation. Already applied changes
remain in the draft and can be undone in the main editor before Save wall set.
The separate wall-coordinate Edit dialog is not affected by this change.

See [deployment](deployment.md) for upgrade and rollback guidance, and
[testing](testing.md) for validation in the installed environment.

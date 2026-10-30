## One-shot room-import action and actual draft comparison

keep_select_values.js used to persist room-import-select and restore it after a
MutationObserver saw the options being rebuilt. Restoration dispatched a synthetic
change event, which invoked the import handler again. Rendering edit mode rebuilt
the options again, creating a feedback loop; Cancel resetting the value could also
be replayed on later observed mutations. Automatic imports could dirty an otherwise
untouched room. The old sticky dirty flag additionally stayed true after undo.

room-import-select is now excluded from both capture persistence and restoration,
including previously stored values. The handler consumes the selected value before
rendering/confirm, ignores reentrant invocations, and treats identical draft content
as a no-op. Dirty state is derived from the active edit fields versus saved room
values and recomputed at destructive-action/navigation checks. Name trimming and
newline normalization match editor/server behavior; Markdown whitespace remains
significant. show() resets clean state. The shared restoration policy for ordinary
selects is unchanged. No API, database or fog changes are involved.

### Imported notes picker inside the editor

room-import-choice is now a child of room-form, before the name field. Its
visibility follows editMode rather than read mode, and the action handler refuses
imports outside editing. Form save enable/disable handling now includes select
controls. Selection stays a one-shot, non-restored action; genuine draft-difference
confirmation, reentrancy guards and Cancel semantics are unchanged.


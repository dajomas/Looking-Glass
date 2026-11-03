## Imported names already assigned to rooms

room_note_import.list_entries adds assigned flags from all persisted room_notes
names in the same map (trimmed and casefolded). This recognizes assignments made
before the patch and manual matching names without introducing import-ID bindings
or a migration. All same-name import variants share availability. Preserved
inactive geometry records remain conservative reservations.

The editor filters flags for both rendering and action lookup. It refreshes the
library when entering edit mode, after successful saves and on import; the existing
load generation guard discards stale responses. A final render after re-enabling
save controls restores correct no-options/disabled state. Selection is still a
one-shot draft action excluded from dropdown remembering. This is not a uniqueness
constraint: simultaneous/manual duplicate saves remain possible as before.


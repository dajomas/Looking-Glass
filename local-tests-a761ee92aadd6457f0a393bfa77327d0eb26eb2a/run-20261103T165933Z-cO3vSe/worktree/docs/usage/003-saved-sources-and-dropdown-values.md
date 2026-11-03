## Saved sources and dropdown values

Save wall sources once in the campaign, choose a saved source and wall set,
and apply. Wall sets are naturally alphabetised while retaining their original
import indices. Applying does not ask for confirmation. The same source/set can
be used for several maps; applying affects only its target map. The removed
one-off importer is not restored by this update. The saved-source file chooser
explicitly accepts a Foundry VTT / UVTT (Universal VTT) file; save it as a reusable
source before selecting a wall set. The legend names non-blocking walls
“Ethereal / passive”; this is a label clarification, not a new wall type.

Valid selected values stay visible after Apply, source-list refresh and page
reload. Browser-local choices are keyed by page, target map and (for wall sets)
source ID. A choice is restored only if its option still exists and the dropdown
is ready. Changing source cannot restore a set from a different source. Choosing
the blank option explicitly clears that preference. The map switch remains
server/URL-authoritative, not restored to a different map by browser storage.
Browser storage can be unavailable; the controls still work without persistence.
This is UI selection memory, not a database association inferred from the menu.


## Imported-name availability

Library list/import response entries now include `assigned: boolean` alongside
id/name/markdown. All entries remain present in the API; the editor filters out
assigned ones. The flag matches saved room_notes names in the same map using
Python strip().casefold(), including the current room, manual assignments and
preserved inactive geometry records. It does not inspect note content or reserve
drafts. Clearing/renaming a saved name changes availability on the next fetch.
No schema, route or permission changes; existing saves are not uniqueness-locked.


## Imported-name availability tests

python/tests/test_room_note_availability.py covers pre-existing/manual matching
names, case/whitespace normalization, same-name variants, per-map scope, rename,
clear, duplicate saved names and retaining original library entries. The UI test
checks hiding assigned options, ignoring unavailable action IDs and disabling
an exhausted dropdown. HTTP integration coverage checks assigned flags after
save and clear; full FastAPI dependencies are required to run that file.


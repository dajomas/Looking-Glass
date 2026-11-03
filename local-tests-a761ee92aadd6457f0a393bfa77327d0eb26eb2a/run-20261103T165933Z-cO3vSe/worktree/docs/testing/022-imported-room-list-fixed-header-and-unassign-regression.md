## Imported-room list fixed header and unassign regression

Run from the repository root:

```sh
node python/tests/test_room_library_manager.js
cd python
python -m pytest -q tests/test_room_library_unassign.py tests/test_room_library_layout.py
python -m pytest -q tests/test_room_library_unassign_web.py
```

Service tests cover normalized/all-matching names, duplicate imported names, revision
increments, idempotence, wrong-map/missing entries, import retention, other-map
isolation and rollback. JS tests cover confirmations, draft blocking, safe text,
selected-room/overlay refresh and errors. HTTP tests cover owner/CSRF checks, stale
save rejection and unchanged fog; they require installed web/dev dependencies.

Manual browser acceptance: import many notes, open the list, scroll to the bottom
and verify heading/Close/Refresh/status remain visible. Test keyboard scrolling,
a small viewport, and closed/reopened dialog visibility. Cancel unassign, then
confirm it; check the room is unnamed with empty notes, the library entry is
available, and player fog is identical. Try custom saved notes, duplicate names,
a selected room, dirty draft, and another map. Assigned entries must still resist
deletion until unassigned. Browser layout and HTTP checks were not run in the build
environment; service/static-layout and Node tests were run (see Patch notes).


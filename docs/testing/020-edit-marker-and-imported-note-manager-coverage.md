## Edit marker and imported-note manager coverage

python/tests/test_room_library_tools.py verifies an edit mask highlights only its
room without changing labels, deletion refuses assigned/wrong-map entries, names
remain protected when notes differ, and allowed deletion leaves map rooms/fog
untouched. node python/tests/test_room_edit_marker.js covers highlight lifecycle,
late responses, geometry invalidation and errors. node
python/tests/test_room_library_manager.js covers all-entry listing, safe source text,
assigned-button protection, deletion Cancel/success and changed-assignment errors.
The room-note harness checks edit-mode transition callbacks. HTTP integration tests
were extended for overlay invariance, stale geometry, deletion CSRF/access and
assigned protection, and require the full installed FastAPI dev dependencies.


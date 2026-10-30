## Name coverage overlay regression tests

python/tests/test_room_name_overlay.py verifies green/red classification, note-only
and whitespace-name handling, geometry-detached records, counts, transparent walls,
clear transitions and unchanged label data. The HTML placement test checks the
button immediately follows the checkbox and starts hidden/unpressed. node
python/tests/test_room_name_overlay.js exercises toggle show/hide, unchecking,
counts, geometry refresh, failures and stale-response suppression. Existing HTTP
coverage was extended for the GET overlay, permission refusal and fog invariance.


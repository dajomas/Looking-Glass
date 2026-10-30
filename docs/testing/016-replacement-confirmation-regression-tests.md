## Replacement confirmation regression tests

Run `node python/tests/test_keep_select_values.js` and
`node python/tests/test_room_notes.js` from the repository root. The first test
seeds an old remembered imported choice, simulates observed mutations and checks
that it never dispatches a synthetic change while ordinary dropdown restoration
still works. With the pre-fix helper this test produced 10 replays before its
bounded drain stopped it; with the fix it passes without any replay.

Room tests cover saved replacement without warning, edit/undo clean state, a real
unsaved draft, one prompt on OK/Cancel, consumed/reentrant events, and identical
import selection. Existing paste/clear/save/import behavior is also covered.


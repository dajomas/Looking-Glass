## Double Reveal fog-mode regressions

Run from the repository root:

```sh
node python/tests/test_double_reveal.js
node python/tests/test_double_reveal_fog.js
python -m pytest -q python/tests/test_double_reveal.py python/tests/test_double_reveal_web.py python/tests/test_double_reveal_fog_templates.py
```

The new Node regression checks marker phases/scale, one action per click, rapid/concurrent
calls, confirmation/cancellation, travel preconditions, hidden-room artwork, invalid and
unconfigured rooms, remote phase changes, read/write failures, mode exclusion, Done and
production click routing without fallthrough. Template checks cover admin-only assets,
script order, wrapping CSS and absence of the removed description.

Manual browser checks: configure a room/destination, reveal fog, verify amber 2, Ctrl-click
to reveal true artwork, verify cyan ↗, then cancel/confirm travel. Check player screens
have no badges/legend and destination fog/artwork are preserved. Check hidden rooms,
inactive maps, unlinked rooms, remote edits, selection-mode handoff, zoom/pan and narrow
sidebars. Plain double-click zoom/doors must retain behavior, while a rapid Ctrl double-click
must not reveal+travel. DOM/source checks do not prove visual layout or native event timing.
HTTP tests need development/runtime dependencies; skipped tests are not passing tests.

